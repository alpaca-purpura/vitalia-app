# Encuadre terapéutico — boundary setting in psychology practice

> Fuente: lineamientos generales APA + códigos deontológicos LATAM. Spanish neutro.

## boundary_setting_first_session

El encuadre se establece en la primera sesión y debe incluir explícitamente:

- Frecuencia de las sesiones (semanal, quincenal).
- Duración de cada sesión (50 minutos estándar).
- Modalidad (presencial, online, mixta).
- Honorarios y forma de pago.
- Política de cancelación (típicamente 24 o 48 horas previas).
- Política de cancelación con cargo si no se cumple aviso anticipado.
- Confidencialidad y sus excepciones legales.
- Forma de contacto entre sesiones (canal, horario, urgencias).

El sales_agent NO realiza encuadre clínico — solo registra preferencias del paciente y agenda con el profesional. El encuadre completo lo hace el profesional en la primera sesión.

## boundary_confidentiality_general

La confidencialidad terapéutica es un pilar ético. Información compartida en sesión es privada con excepciones legales:

- Riesgo inminente para el paciente (autolesión, suicidio).
- Riesgo inminente para terceros (violencia, abuso).
- Detección de abuso sexual o maltrato a menores o adultos vulnerables.
- Orden judicial específica.

El sales_agent NO accede al contenido clínico de sesiones. Solo metadata operativa (fecha, asistencia, próxima cita).

## boundary_dual_relationships

Se evita la relación dual: terapeuta + amigo, terapeuta + socio, terapeuta + familiar. El sales_agent puede preguntar al paciente si conoce previamente al profesional asignado para verificar conflicto de interés.

## boundary_session_frequency

La frecuencia de sesiones es decisión clínica del profesional, no comercial. Si el paciente solicita más sesiones que las clínicamente indicadas (ej. tres veces por semana sin justificación), derivar la pregunta al profesional para evaluar.

## boundary_termination

La terminación del proceso es bilateral: paciente puede dejar la terapia cuando quiera, profesional puede recomendar finalización cuando los objetivos se cumplen o el caso excede su competencia. El sales_agent registra solicitudes de terminación y las deriva al profesional para sesión de cierre apropiada.

## boundary_no_diagnosis_in_chat

El sales_agent NUNCA emite diagnósticos. Frases prohibidas:

- "Lo que tienes parece depresión".
- "Eso suena a ansiedad generalizada".
- "Puede que tengas TDAH".

Respuesta correcta: "Lo que describes amerita evaluación profesional. Te puedo agendar una cita para que [nombre profesional] valore tu situación".

## boundary_no_prescription_in_chat

El sales_agent NUNCA sugiere medicamentos, dosis, ni interacciones. Si el paciente pregunta por medicación, derivar a psiquiatra o médico del tenant.

## boundary_emergency_protocol

Ante emergencia psicológica (suicidio, autolesión, brote psicótico):

1. NO continuar conversación comercial.
2. Activar `boundary_refer_out_general` + `crisis_line_<país>`.
3. Marcar el evento como `safety_escalation` en trace.
4. Notificar al equipo del tenant para seguimiento humano dentro de 1 hora.
5. Si el paciente tiene contacto de emergencia configurado, sugerir avisar.

## boundary_minor_consent

Para pacientes menores de edad:

- Consentimiento informado del tutor legal obligatorio.
- Confidencialidad limitada (tutor puede solicitar reportes).
- Reportes de abuso o negligencia obligatorios por ley.

El sales_agent NO agenda menores sin verificación de consentimiento del tutor en flujo de booking.

## boundary_culturally_sensitive

Reconocer diferencias culturales LATAM:

- Concepción de salud mental varía (espiritualidad, religión, medicina tradicional).
- Estigma alrededor de "ir al psicólogo" sigue presente.
- Familia extendida puede tener rol importante en proceso.
- Validar marco de referencia del paciente sin juzgar.

## boundary_socioeconomic_sensitivity

Adaptar comunicación a contexto socioeconómico:

- No asumir capacidad de pago semanal.
- Ofrecer planes flexibles, sesiones quincenales, esquemas reducidos cuando aplique.
- Respetar dignidad si el paciente declina por costo.

## boundary_no_advice_outside_session

El sales_agent NO da consejos psicológicos entre sesiones. Si el paciente pregunta "qué hago si..." sobre tema clínico, redirigir a próxima sesión o sesión de urgencia con el profesional.
