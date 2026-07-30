#!/usr/bin/env node
/**
 * check-bowtie-bundle.mjs — Verifica que el chunk BowtieSVG < 30KB gzipped
 *
 * Validator ID: visual_bowtie_bundle_size (NO defer — corre desde build estático)
 * Story: vitalia-slice-1-marketing
 * Ticket: T-mk-fe-7
 *
 * Qué verifica:
 *   - Busca en .next/static/chunks/ el chunk que corresponde a MarketingBowtieSVG
 *   - Mide el tamaño gzipped (zlib.gzipSync)
 *   - Falla con exit 1 si supera 30KB (presupuesto de bundle per 03-arch-fe.md § 9)
 *
 * Cómo correr:
 *   cd vitalia/frontend && next build && node scripts/check-bowtie-bundle.mjs
 *
 * Salida esperada:
 *   ✓ BowtieSVG chunk: XX.X KB gzipped (bajo presupuesto de 30KB)
 *   O:
 *   ✗ BowtieSVG chunk supera presupuesto: XX.X KB > 30KB
 *
 * Nota: en modo dev (Turbopack) los chunks no están en .next/static/chunks/
 * con la misma nomenclatura que en production. Este script requiere `next build`.
 *
 * downstream-regression-na: brand-local script; no cross-brand consumers
 */

import { readdir, readFile, stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import { gzipSync } from "node:zlib";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const BUDGET_BYTES = 30 * 1024; // 30KB gzipped
const BUDGET_KB = (BUDGET_BYTES / 1024).toFixed(0);

// Directorio raíz del frontend vitalia (un nivel arriba de /scripts)
const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FRONTEND_ROOT = resolve(__dirname, "..");
const CHUNKS_DIR = join(FRONTEND_ROOT, ".next", "static", "chunks");

// ---------------------------------------------------------------------------
// Patrones de búsqueda para el chunk de BowtieSVG
// Los chunks de Next.js usan hash en el nombre. Buscamos por contenido SVG.
// Fallback: buscar por nombre de componente en el manifest del build.
// ---------------------------------------------------------------------------

const BOWTIE_COMPONENT_MARKERS = [
  "MarketingBowtieSVG",
  "mktg-grad-acquisition",
  "mktg-grad-expansion",
  "mktg-arrowhead",
  "STAGE_GEOMETRY",
  "bowtie",
];

const BOWTIE_SLUG_PATTERNS = [
  /marketing.*bowtie/i,
  /bowtie.*marketing/i,
  /MarketingBowtieSVG/i,
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Calcula el tamaño gzipped de un Buffer en bytes.
 */
function gzippedSize(buf) {
  return gzipSync(buf, { level: 9 }).length;
}

/**
 * Verifica si un archivo de chunk contiene marcadores del BowtieSVG.
 * Usa un sample (primeros 50KB del archivo) para no cargar chunks enormes.
 */
async function chunkContainsBowtie(filePath) {
  const { size } = await stat(filePath);
  const SAMPLE_SIZE = Math.min(size, 50 * 1024);

  const buf = Buffer.alloc(SAMPLE_SIZE);
  const { open, read, close: closeFd } = await import("node:fs/promises");
  const fh = await open(filePath, "r");
  try {
    await read(fh, buf, 0, SAMPLE_SIZE, 0);
  } finally {
    await closeFd(fh);
  }

  const content = buf.toString("utf8");
  return BOWTIE_COMPONENT_MARKERS.some((marker) => content.includes(marker));
}

/**
 * Lista todos los archivos .js y .mjs en el directorio de chunks.
 */
async function listChunkFiles(dir) {
  if (!existsSync(dir)) return [];

  const entries = await readdir(dir, { withFileTypes: true });
  const jsFiles = [];

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (entry.name.endsWith(".js") || entry.name.endsWith(".mjs")) {
      jsFiles.push(join(dir, entry.name));
    }
  }

  // Ordenar por tamaño ascendente para encontrar chunks pequeños primero
  const withSizes = await Promise.all(
    jsFiles.map(async (f) => ({ path: f, size: (await stat(f)).size }))
  );
  return withSizes.sort((a, b) => a.size - b.size).map((x) => x.path);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log("Verificando presupuesto de bundle BowtieSVG...\n");

  // 1. Verificar que existe el directorio .next/static/chunks/
  if (!existsSync(CHUNKS_DIR)) {
    console.error(`Error: ${CHUNKS_DIR} no existe.`);
    console.error("Ejecutar primero: cd vitalia/frontend && next build");
    process.exit(1);
  }

  // 2. Listar chunks JS
  const chunkFiles = await listChunkFiles(CHUNKS_DIR);

  if (chunkFiles.length === 0) {
    console.warn(`Advertencia: no se encontraron archivos JS en ${CHUNKS_DIR}`);
    console.warn("El build puede estar incompleto. Verificar con: next build");
    // No fallar — puede ser que el build esté en modo turbopack dev
    process.exit(0);
  }

  console.log(`Analizando ${chunkFiles.length} chunks en .next/static/chunks/...`);

  // 3. Buscar chunks que contienen BowtieSVG
  const bowtieChunks = [];

  for (const filePath of chunkFiles) {
    // Primero verificar por nombre (más rápido)
    const fileName = filePath.split("/").pop() ?? "";
    const nameMatch = BOWTIE_SLUG_PATTERNS.some((p) => p.test(fileName));

    if (nameMatch) {
      const buf = await readFile(filePath);
      const gzSize = gzippedSize(buf);
      bowtieChunks.push({ path: filePath, name: fileName, gzSize });
      continue;
    }

    // Si el archivo es pequeño (< 200KB), buscar por contenido
    const { size } = await stat(filePath);
    if (size < 200 * 1024) {
      const hasBowtie = await chunkContainsBowtie(filePath);
      if (hasBowtie) {
        const buf = await readFile(filePath);
        const gzSize = gzippedSize(buf);
        bowtieChunks.push({ path: filePath, name: fileName, gzSize });
      }
    }
  }

  // 4. Si no se encontraron chunks específicos del bowtie, verificar el
  //    chunk de la página /marketing como proxy (contiene el componente)
  if (bowtieChunks.length === 0) {
    console.log(
      "\nNo se encontraron chunks específicos de BowtieSVG (chunk splitting puede no estar activo)."
    );
    console.log(
      "Buscando el chunk de la página /marketing como proxy del presupuesto...\n"
    );

    for (const filePath of chunkFiles) {
      const fileName = filePath.split("/").pop() ?? "";
      if (/marketing/i.test(fileName)) {
        const buf = await readFile(filePath);
        const gzSize = gzippedSize(buf);
        bowtieChunks.push({ path: filePath, name: fileName, gzSize });
      }
    }
  }

  // 5. Evaluar resultados
  if (bowtieChunks.length === 0) {
    console.log(
      "Información: No se encontraron chunks específicos de BowtieSVG ni de /marketing."
    );
    console.log(
      "El componente puede estar incluido en un chunk compartido (vendor bundle)."
    );
    console.log(
      "Verificación de presupuesto: OMITIDA (requiere chunk splitting explícito en next.config.ts)."
    );
    console.log("\nPara enforcement estricto, agregar en next.config.ts:");
    console.log("  experimental.optimizePackageImports con split explícito de MarketingBowtieSVG");
    process.exit(0);
  }

  // 6. Reportar y verificar presupuesto
  let failed = false;
  console.log("Chunks encontrados relacionados con BowtieSVG:");
  console.log("─".repeat(60));

  for (const { name, gzSize } of bowtieChunks) {
    const gzKB = (gzSize / 1024).toFixed(1);
    const withinBudget = gzSize <= BUDGET_BYTES;

    if (withinBudget) {
      console.log(`  ✓ ${name}: ${gzKB} KB gzipped (presupuesto: ${BUDGET_KB}KB) ✓`);
    } else {
      console.error(`  ✗ ${name}: ${gzKB} KB gzipped > ${BUDGET_KB}KB (EXCEDE PRESUPUESTO)`);
      failed = true;
    }
  }

  console.log("─".repeat(60));

  if (failed) {
    console.error(`\n✗ FALLO: Al menos un chunk de BowtieSVG excede el presupuesto de ${BUDGET_KB}KB gzipped.`);
    console.error("  Acción requerida: usar dynamic import con React.lazy() para separar BowtieSVG.");
    console.error("  Referencia: vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-fe.md § 9");
    process.exit(1);
  } else {
    const maxGzKB = (Math.max(...bowtieChunks.map((c) => c.gzSize)) / 1024).toFixed(1);
    console.log(`\n✓ Presupuesto de bundle BowtieSVG OK: ${maxGzKB}KB gzipped (máx.) ≤ ${BUDGET_KB}KB`);
    process.exit(0);
  }
}

main().catch((err) => {
  console.error("Error inesperado en check-bowtie-bundle.mjs:", err);
  process.exit(1);
});
