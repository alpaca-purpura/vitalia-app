<!-- voseo-allowed: contiene transcript verbatim de Chris (notas voseo natural) + Claude responses (tuteo) — escape per spanish-text.md R25 -->
---
story_id: vitalia-fase2-valeria-pacientes
created_at: 2026-05-27T14:30:00-05:00
last_modified: 2026-05-27T18:25:23-05:00
notes_count: 2
refs_count: 5
conversation_count: 5
migration_note: "chris-input.md populado con contenido real del mockup v0.5.2 (sesión iterativa 2026-05-27)"
---

# chris-input.md · vitalia-fase2-valeria-pacientes

> Sub-tab Pacientes activa. Directorio paginado con búsqueda + segmentos (Todos · Deudores · Tratamientos activos), ficha workspace N3-dyn con tabs.
>
> Cap target: `valeria.pacientes` · Cap change type: `new`.

## 💭 Notas

### 2026-05-27 14:30
Necesito que el estado de pago se vea PROMINENTE en el directorio porque Valeria entra a la mañana y lo primero que mira es quién no pagó.

Filtros por etiqueta (VIP, primera vez, post-tratamiento) son importantes para Valeria.

### 2026-05-27 16:00
También me gustaría poder hacer quick-action de cobrar deuda desde el directorio sin entrar a la ficha. Pensemos esto.

## 📎 Referencias

- **🔗 link** · https://intercom.com/help/customer-segments
  > me gusta cómo segmentan acá
- **🖼 img** · refs/2026-05-27-mockup-directorio.png
  > boceto que hice anoche
- **📖 story-ref** · F2-S1
  > la integración con agenda debe ser fluida
- **💬 text** · Marta (buyer persona): "no me importa el detalle médico, importa quién tiene cita esta semana"
- **📚 learning-ref** · 2026-05-18-phi-repository-base
  > reusar el masking pattern

## 💬 Conversación

### 2026-05-27 14:30 · 🧑 chris
Ver mis notas + referencias arriba.

### 2026-05-27 14:42 · 🤖 claude · `/po-ux` · ✓ APLICADO
Apliqué tus inputs a draft 01-spec.md:
- SC-08: estado de pago como pill prominente en card directorio
- SC-09: filtros segmentos VIP / primera vez / post-tratamiento
- AC-12: quick-action "marcar pagado" desde directorio (basado en nota de 16:00)
- AC-13: integración con valeria.agenda (link "Ver próxima cita" en ficha)

Reusé `BasePhiRepository` per tu learning-ref.

### 2026-05-27 14:43 · 🤖 claude · `/po-ux` · ⚠️ DUDA
La regla "no detalle médico" de Marta — ¿aplica solo al directorio (listas) o también a la ficha de paciente?

Mi propuesta: solo al directorio. La ficha sí muestra info médica bajo role doctor/nurse. ¿Confirmás?

### 2026-05-27 14:50 · 🧑 chris
Confirmado: solo directorio. Ficha mantiene full reveal bajo role doctor/nurse (como regla anterior).

### 2026-05-27 14:52 · 🤖 claude · `/po-ux` · ✓ APLICADO
Actualizado SC-08:
- PHI masking SOLO en directorio (lista)
- Ficha full reveal bajo role doctor|nurse|admin

Spec listo para ratificación. Te dejo 01-spec.md draft completo · revísalo en cockpit tab 📝 Spec.
