# Derivación clínica — referral protocols

> Fuente: protocolos generales de derivación profesional. Spanish neutro LATAM.
> Brand-scope: contenido de referencia clínica compartido entre todos los tenants Vitalia.

## boundary_refer_out_general

Si una persona expresa pensamientos de hacerse daño, ideas suicidas, autolesión o se encuentra en una crisis emocional severa, NO continúes la conversación comercial. La respuesta segura es:

1. Validar la angustia con calidez ("Lamento mucho que estés pasando por esto").
2. Ofrecer la línea de emergencia local correspondiente al país del paciente.
3. Sugerir contacto inmediato con un profesional de salud mental humano o servicio de urgencia.
4. NO ofrecer diagnóstico, NO ofrecer prescripción, NO sustituir contacto humano profesional.
5. Registrar el evento como `safety_escalation` en el trace para auditoría.

Este chunk se recupera SIEMPRE que se detecten palabras clave de crisis en el mensaje del paciente. Tiene prioridad sobre cualquier flujo comercial activo (booking, follow-up, payment).

## referral_to_psychiatrist

La derivación a psiquiatra (no psicólogo) es apropiada cuando:

- El paciente reporta síntomas que sugieren necesidad de evaluación farmacológica (insomnio severo, episodios maníacos, alucinaciones).
- Hay diagnóstico previo de trastorno mental grave (TBP, esquizofrenia, depresión mayor) sin medicación actual.
- El paciente solicita explícitamente medicación.

NUNCA prescribir o sugerir medicamentos específicos. Solo derivar al especialista habilitado del tenant.

## referral_to_specialized_therapy

La derivación a terapia especializada (TEPT, TCA, parejas, familia) es apropiada cuando el motivo de consulta excede el alcance del profesional asignado actualmente. Sugerir agendar con el especialista correspondiente del tenant si está disponible, o derivar fuera del tenant si no.

## referral_to_general_practitioner

Si los síntomas reportados podrían tener causa orgánica (fatiga extrema, dolor de cabeza persistente, pérdida de peso inexplicada), sugerir evaluación médica general antes de profundizar en lo psicológico.

## documentation_of_referral

Toda derivación debe registrarse en `copilot_trace_event.context_used` con:

- Razón de la derivación.
- Tipo de profesional sugerido.
- Si se ofreció línea de emergencia (sí/no + país).
- Si se notificó al equipo del tenant para seguimiento humano.
