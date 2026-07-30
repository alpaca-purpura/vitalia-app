# Spanish neutro — glosario voseo→neutro completo (moved from .claude/rules/ 2026-05-30, load on-demand)

Glosario completo. La rule slim (`.claude/rules/spanish-text.md`) tiene R1/R2 + subset alta-frecuencia + magic comment. Esto se lee on-demand cuando hay duda sobre una conversión específica. El pre-commit hook enforce voseo mecánicamente igual.

| Voseo | Neutro | Voseo | Neutro |
|---|---|---|---|
| vos | tú | sos | eres |
| tenés | tienes | querés | quieres |
| podés | puedes | sabés | sabes |
| hacés | haces | venís | vienes |
| decís | dices | mirá | mira |
| dejá/dejalo | deja/déjalo | poné/ponelo | pon/ponlo |
| usá/usalo | usa/úsalo | hacé/hacelo | haz/hazlo |
| elegí/elegilo | elige/elígelo | seleccioná | selecciona |
| arrancá/empezá | empieza/comienza | agregá | agrega |
| configurá | configura | revisá | revisa |
| escribí | escribe | guardá | guarda |
| subí/bajá | sube/baja | abrí | abre |
| volvé | vuelve | andá | ve |
| cambiá/cambialo | cambia/cámbialo | ofrecés/cobrás | ofreces/cobras |
| ejecutás/acompañás | ejecutas/acompañas | activás/desactivás | activas/desactivas |
| linkeá | enlaza | despublicala/reactivá | despublícala/reactiva |
| cancelala | cancélala | validá/considerá | valida/considera |
| formulala | formúlala | marcá | marca |
| referís | llamas/te refieres | atendés | atiendes |
| integrás | integras | listá | lista |
| probá | prueba | mostrá | muestra |
| compartí | comparte | contá | cuenta |
| explicá | explica | fijate | revisa/ten en cuenta |
| acordate | recuerda | dale (imperativo) | asígnale/ponle/define |

## Magic comment escape (R25 2026-05-05) — detalle

Files que citan glosario voseo verbatim como referencia (rules MD, audit review reports, test fixtures que prueban detección voseo) — pre-commit hook honra magic comment en cualquiera de estas formas:

```python
# voseo-allowed                       # Python comment, no reason
# voseo-allowed: optional reason      # Python comment, with reason after colon
# voseo-allowed — optional reason     # any unicode separator + reason
```

```markdown
<!-- voseo-allowed -->                <!-- Markdown, no reason -->
<!-- voseo-allowed: optional -->      <!-- Markdown, with reason inside -->
<!-- voseo-allowed — reason -->       <!-- any unicode separator + reason -->
```

Magic comment debe aparecer en cualquier línea del archivo (no anchored a top). Hook regex (línea 105 `scripts/git-hooks/pre-commit`):

```bash
grep -qE '(#\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)' "${FILE}"
```

**Cuándo NO usar:** user-facing strings (UI labels/copy/email/notification). Magic comment es escape para **referencia técnica del glosario** (audit reports, rules docs, test fixtures que prueban hook). Si tu archivo genuinamente requiere voseo en string user-facing → revisa si pertenece a sales_agent voice (excepción). Si NO sales_agent → fix the voseo, no marquees con magic comment.

Tests: `backend/tests/scripts/test_pre_commit_hook.py` cubre 4 variantes (no-reason, with-reason, em-dash, plain block).
