// devhub-sidecar — sesiones de agente de DevHub (P2), supervisado por el binario Go.
// SPEC: products/devhub/specs/delivery-cockpit.md (RN-35..RN-38). Powered by Claude
// Agent SDK — branding propio (frontera #6 del norte): esto NO es ni se llama Claude Code.
//
// Contrato (HTTP loopback, JSON):
//   GET  /salud          → {ok, auth, sesiones}
//   POST /sesiones       → 201 {id}   (lanza UNA sesión parametrizada)
//   GET  /sesiones       → lista resumida
//   GET  /sesiones/{id}  → {id, meta, estado, eventos[], workspace, resultado?}
//
// Handshake con el supervisor: imprime "SIDECAR_PORT=<n>" en stdout al escuchar (RN-35).
// Workspace aislado por sesión en ~/.prenter/devhub/sesiones/<id>/ (RN-38): la sesión
// jamás lee el repo (contexto = COPIAS) ni transiciona stories (RN-31 intacto).

import { query } from '@anthropic-ai/claude-agent-sdk';
import * as http from 'node:http';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';

// ── auth (RN-36): contrato producto = API key; credencial-local = solo dogfood I-76 ──

function detectarAuth(): 'api-key' | 'credencial-local' | 'ninguna' {
  if (process.env.ANTHROPIC_API_KEY) return 'api-key';
  if (process.env.CLAUDE_CODE_USE_BEDROCK || process.env.CLAUDE_CODE_USE_VERTEX) return 'api-key';
  if (fs.existsSync(path.join(os.homedir(), '.claude', '.credentials.json'))) return 'credencial-local';
  return 'ninguna';
}

// ── modelo de sesión ──────────────────────────────────────────────────────────

interface FuenteContexto {
  nombre: string;
  ruta_abs: string;
}

interface Evento {
  ts: string;
  tipo: 'init' | 'texto' | 'herramienta' | 'resultado' | 'error';
  detalle: string;
}

interface Sesion {
  id: string;
  meta: Record<string, unknown>;
  estado: 'creada' | 'corriendo' | 'terminada' | 'error';
  inicio: string;
  workspace: string;
  eventos: Evento[];
  resultado?: { resumen: string; salida: string[] };
}

const sesiones = new Map<string, Sesion>();

const RAIZ_SESIONES = path.join(os.homedir(), '.prenter', 'devhub', 'sesiones');

function nuevoID(): string {
  const t = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  return `s-${t}-${Math.random().toString(36).slice(2, 6)}`;
}

function recortar(s: string, max = 400): string {
  const limpio = s.replace(/\s+/g, ' ').trim();
  return limpio.length > max ? limpio.slice(0, max) + '…' : limpio;
}

function anotar(sesion: Sesion, tipo: Evento['tipo'], detalle: string) {
  const ev: Evento = { ts: new Date().toISOString(), tipo, detalle };
  sesion.eventos.push(ev);
  fs.appendFileSync(path.join(sesion.workspace, 'eventos.jsonl'), JSON.stringify(ev) + '\n');
}

// ── la sesión (RN-38): workspace aislado, tools acotados, no-interactiva ──────

async function correrSesion(sesion: Sesion, prompt: string) {
  sesion.estado = 'corriendo';
  try {
    const q = query({
      prompt,
      options: {
        cwd: sesion.workspace,
        maxTurns: 25,
        permissionMode: 'acceptEdits',
        allowedTools: ['Read', 'Write', 'Edit', 'Glob', 'Grep'],
        disallowedTools: ['Bash', 'WebFetch', 'WebSearch', 'Task'],
        settingSources: [], // no carga CLAUDE.md/settings del operador — sesión hermética
      },
    });
    for await (const msg of q as AsyncIterable<any>) {
      if (msg.type === 'system' && msg.subtype === 'init') {
        anotar(sesion, 'init', `modelo ${msg.model} · sesión SDK ${msg.session_id}`);
      } else if (msg.type === 'assistant') {
        for (const bloque of msg.message?.content ?? []) {
          if (bloque.type === 'text' && bloque.text?.trim()) {
            anotar(sesion, 'texto', recortar(bloque.text));
          } else if (bloque.type === 'tool_use') {
            anotar(sesion, 'herramienta', `${bloque.name}: ${recortar(JSON.stringify(bloque.input ?? {}), 200)}`);
          }
        }
      } else if (msg.type === 'result') {
        const dur = Math.round((msg.duration_ms ?? 0) / 1000);
        anotar(sesion, 'resultado', `${msg.subtype} · ${msg.num_turns} turnos · ${dur}s`);
        const salidaDir = path.join(sesion.workspace, 'salida');
        const salida = fs.existsSync(salidaDir) ? fs.readdirSync(salidaDir).sort() : [];
        sesion.resultado = { resumen: recortar(msg.result ?? '(sin texto final)', 600), salida };
        sesion.estado = msg.is_error ? 'error' : 'terminada';
      }
    }
    if (sesion.estado === 'corriendo') {
      // el stream terminó sin mensaje result — no inventamos éxito
      anotar(sesion, 'error', 'stream terminó sin resultado');
      sesion.estado = 'error';
    }
  } catch (err: any) {
    anotar(sesion, 'error', recortar(String(err?.message ?? err)));
    sesion.estado = 'error';
  }
}

function crearSesion(body: { prompt: string; contexto?: FuenteContexto[]; meta?: Record<string, unknown> }): Sesion {
  const id = nuevoID();
  const workspace = path.join(RAIZ_SESIONES, id);
  fs.mkdirSync(path.join(workspace, 'contexto'), { recursive: true });
  fs.mkdirSync(path.join(workspace, 'salida'), { recursive: true });
  fs.writeFileSync(path.join(workspace, 'PROMPT.md'), body.prompt);
  for (const f of body.contexto ?? []) {
    // COPIA (RN-38): la sesión jamás toca los originales del repo
    const destino = path.join(workspace, 'contexto', path.basename(f.nombre));
    try {
      fs.copyFileSync(f.ruta_abs, destino);
    } catch {
      fs.writeFileSync(destino + '.ausente', `fuente ilegible: ${f.ruta_abs}\n`);
    }
  }
  const sesion: Sesion = {
    id,
    meta: body.meta ?? {},
    estado: 'creada',
    inicio: new Date().toISOString(),
    workspace,
    eventos: [],
  };
  sesiones.set(id, sesion);
  void correrSesion(sesion, body.prompt);
  return sesion;
}

// ── HTTP (RN-37) ──────────────────────────────────────────────────────────────

function json(res: http.ServerResponse, status: number, payload: unknown) {
  const cuerpo = JSON.stringify(payload);
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(cuerpo);
}

function resumen(s: Sesion) {
  return { id: s.id, meta: s.meta, estado: s.estado, inicio: s.inicio, eventos: s.eventos.length };
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url ?? '/', 'http://127.0.0.1');
  if (req.method === 'GET' && url.pathname === '/salud') {
    return json(res, 200, { ok: true, auth: detectarAuth(), sesiones: sesiones.size });
  }
  if (req.method === 'GET' && url.pathname === '/sesiones') {
    return json(res, 200, { sesiones: [...sesiones.values()].map(resumen).reverse() });
  }
  const m = url.pathname.match(/^\/sesiones\/([\w-]+)$/);
  if (req.method === 'GET' && m) {
    const s = sesiones.get(m[1]);
    if (!s) return json(res, 404, { error: 'sesión desconocida' });
    return json(res, 200, s);
  }
  if (req.method === 'POST' && url.pathname === '/sesiones') {
    let cuerpo = '';
    req.on('data', (c) => (cuerpo += c));
    req.on('end', () => {
      let body: any;
      try {
        body = JSON.parse(cuerpo);
      } catch {
        return json(res, 400, { error: 'body JSON inválido' });
      }
      if (typeof body.prompt !== 'string' || !body.prompt.trim()) {
        return json(res, 400, { error: 'prompt requerido' });
      }
      if (detectarAuth() === 'ninguna') {
        // honesto (RN-36): sin credencial no se lanza nada
        return json(res, 503, { error: 'sin credencial: exporta ANTHROPIC_API_KEY (o Bedrock/Vertex)' });
      }
      const s = crearSesion(body);
      return json(res, 201, { id: s.id, workspace: s.workspace });
    });
    return;
  }
  json(res, 404, { error: 'ruta desconocida' });
});

server.listen(0, '127.0.0.1', () => {
  const addr = server.address();
  const puerto = typeof addr === 'object' && addr ? addr.port : 0;
  // handshake con el supervisor Go (RN-35)
  console.log(`SIDECAR_PORT=${puerto}`);
});

for (const señal of ['SIGTERM', 'SIGINT'] as const) {
  process.on(señal, () => {
    server.close();
    process.exit(0);
  });
}

// muerte ligada al supervisor (RN-35): el binario Go retiene nuestro stdin; si el
// binario muere, el pipe se cierra y nos apagamos — cero sidecars huérfanos.
process.stdin.resume();
process.stdin.on('end', () => process.exit(0));
process.stdin.on('close', () => process.exit(0));
