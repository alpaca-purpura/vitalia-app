// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * ParaAdrianView.tsx — Leaf 2: Argumentario para Adrián.
 *
 * El brief de venta del agente: candidatura, argumentario, FAQ, objeciones, keywords.
 * spec §Workspace Pestaña 2 · 01-spec.md §Workspace Pestaña 2
 *
 * Autosave on-change 600ms via useSalesBriefPatch (canon §2.6).
 */

import { useCallback } from "react";
import { Group, GroupHeader, FloatingAutosaveIndicator, Switch } from "@luana/ui-kit";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useAutosave } from "@/hooks/use-autosave";
import {
  useServicioDetail,
  useSalesBriefPatch,
} from "../../../api/servicios";
import type { SalesBriefPatchRequest } from "../../../types/servicios.types";
import { FaqPairList } from "../FaqPairList";
import { ObjecionPairList } from "../ObjecionPairList";
import { TagInput } from "../TagInput";

interface ParaAdrianViewProps {
  offerId: string;
}

export function ParaAdrianView({ offerId }: ParaAdrianViewProps) {
  const { data: servicio } = useServicioDetail({ offerId });
  const { mutateAsync: patchAsync } = useSalesBriefPatch(offerId);

  const saveFn = useCallback(
    (patch: SalesBriefPatchRequest) => patchAsync(patch),
    [patchAsync],
  );
  const { schedule, status } = useAutosave<SalesBriefPatchRequest>({ saveFn });

  const brief = servicio?.sales_brief;

  if (!servicio) {
    return (
      <div className="p-6 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-28 bg-muted rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="p-5 md:p-6 space-y-6 pb-24">
      {/* ── Candidatura & seguridad ─────────────────────────────────────────── */}
      <Group accentVar="--agent-adrian">
        <GroupHeader title="Candidatura y seguridad" />

        <div className="space-y-2">
          <Label htmlFor="candidate_ideal">Candidato ideal</Label>
          <Textarea
            id="candidate_ideal"
            defaultValue={brief?.candidate_ideal ?? ""}
            onChange={(e) => schedule({ candidate_ideal: e.target.value || null })}
            placeholder="Quién es el candidato ideal para este tratamiento…"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="contraindications">Contraindicaciones / quién NO es candidato</Label>
          <Textarea
            id="contraindications"
            defaultValue={brief?.contraindications ?? ""}
            onChange={(e) => schedule({ contraindications: e.target.value || null })}
            placeholder="Condiciones o situaciones que excluyen al paciente…"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="qualification_questions">Preguntas de calificación</Label>
          <Textarea
            id="qualification_questions"
            defaultValue={brief?.qualification_questions ?? ""}
            onChange={(e) =>
              schedule({ qualification_questions: e.target.value || null })
            }
            placeholder="Preguntas que Adrián hace para calificar al prospecto…"
            rows={3}
          />
        </div>

        <div className="flex items-center gap-3">
          <Switch
            id="requires_evaluation"
            defaultChecked={brief?.requires_evaluation ?? false}
            onCheckedChange={(v: boolean) => schedule({ requires_evaluation: v })}
          />
          <Label htmlFor="requires_evaluation" className="cursor-pointer">
            Requiere evaluación previa
          </Label>
        </div>

        <div className="space-y-2">
          <Label htmlFor="escalation_conditions">Condiciones de escalada a humano</Label>
          <Textarea
            id="escalation_conditions"
            defaultValue={brief?.escalation_conditions ?? ""}
            onChange={(e) =>
              schedule({ escalation_conditions: e.target.value || null })
            }
            placeholder="Dolor severo, diagnóstico, medicación — escala al doctor…"
            rows={2}
          />
        </div>
      </Group>

      {/* ── Argumentario ────────────────────────────────────────────────────── */}
      <Group>
        <GroupHeader title="Argumentario" />

        <div className="space-y-2">
          <Label htmlFor="emotional_benefits">Beneficios emocionales</Label>
          <Textarea
            id="emotional_benefits"
            defaultValue={brief?.emotional_benefits ?? ""}
            onChange={(e) => schedule({ emotional_benefits: e.target.value || null })}
            placeholder="El resultado que el paciente realmente compra…"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="pain_of_not_treating">Dolor de no tratarse</Label>
          <Textarea
            id="pain_of_not_treating"
            defaultValue={brief?.pain_of_not_treating ?? ""}
            onChange={(e) =>
              schedule({ pain_of_not_treating: e.target.value || null })
            }
            placeholder="Qué pierde o empeora si no toma acción…"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="differentiators">Diferenciadores</Label>
          <Textarea
            id="differentiators"
            defaultValue={brief?.differentiators ?? ""}
            onChange={(e) => schedule({ differentiators: e.target.value || null })}
            placeholder="Por qué elegir esta clínica sobre las demás…"
            rows={2}
          />
        </div>
      </Group>

      {/* ── FAQ ─────────────────────────────────────────────────────────────── */}
      <Group>
        <GroupHeader title="Preguntas frecuentes" />
        {/* ADR-009: key={offerId} forces remount when entity changes → clean re-seed of local state */}
        <FaqPairList
          key={offerId}
          value={(brief?.faq ?? []).map((f, i) => ({
            id: `faq-${i}`,
            question: f.question,
            answer: f.answer,
          }))}
          onChange={(pairs) => {
            // G2-F12: only persist COMPLETE pairs (domain FaqPair requires both
            // fields non-empty). An empty/partial row stays editable locally but is
            // never sent — adding a blank row no longer fires a save (or a 500).
            const faq = pairs
              .filter((p) => p.question.trim() !== "" && p.answer.trim() !== "")
              .map((p) => ({ question: p.question, answer: p.answer }));
            const current = (brief?.faq ?? []).map((f) => ({
              question: f.question,
              answer: f.answer,
            }));
            if (JSON.stringify(faq) !== JSON.stringify(current)) {
              schedule({ faq });
            }
          }}
        />
      </Group>

      {/* ── Objeciones ──────────────────────────────────────────────────────── */}
      <Group>
        <GroupHeader title="Objeciones y respuestas" />
        {/* ADR-009: key={offerId} forces remount when entity changes → clean re-seed of local state */}
        <ObjecionPairList
          key={offerId}
          value={(brief?.objections ?? []).map((o, i) => ({
            id: `obj-${i}`,
            tag: o.objection_type,
            response: o.response,
          }))}
          onChange={(pairs) => {
            // G2-F12: only persist COMPLETE pairs (domain ObjectionPair requires
            // both fields non-empty). Blank/partial rows never fire a save.
            const objections = pairs
              .filter((p) => p.tag.trim() !== "" && p.response.trim() !== "")
              .map((p) => ({ objection_type: p.tag, response: p.response }));
            const current = (brief?.objections ?? []).map((o) => ({
              objection_type: o.objection_type,
              response: o.response,
            }));
            if (JSON.stringify(objections) !== JSON.stringify(current)) {
              schedule({ objections });
            }
          }}
        />
      </Group>

      {/* ── Para el match ────────────────────────────────────────────────────── */}
      <Group>
        <GroupHeader title="Para el match" />

        <div className="space-y-2">
          <Label>Palabras clave / sinónimos</Label>
          <TagInput
            value={brief?.keywords ?? []}
            onChange={(tags) => schedule({ keywords: tags })}
            placeholder="Agrega sinónimos con Enter…"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="problems_solved">Problemas que resuelve</Label>
          <Textarea
            id="problems_solved"
            defaultValue={brief?.problems_solved ?? ""}
            onChange={(e) => schedule({ problems_solved: e.target.value || null })}
            placeholder="Síntomas o problemas que busca el paciente…"
            rows={2}
          />
        </div>
      </Group>

      {/* Autosave indicator — ONE per page (canon §2.6) */}
      <FloatingAutosaveIndicator status={status} />
    </div>
  );
}
