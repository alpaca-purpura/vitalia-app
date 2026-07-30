# Trastornos depresivos — descripciones clínicas para referencia

> Spanish neutro LATAM. Brand-scope. Información educativa. NO diagnóstica.

## depression_overview

La depresión clínica es más que tristeza pasajera. Es un trastorno con base biopsicosocial que afecta el estado de ánimo, el pensamiento, el cuerpo, el comportamiento y las relaciones. Prevalencia vital ~15%; mayor en mujeres (2:1).

## depression_major_episode_description

Episodio depresivo mayor: duración mínima 2 semanas con 5 o más síntomas (al menos uno: ánimo deprimido o anhedonia):

- Ánimo deprimido casi todo el día.
- Pérdida de interés o placer (anhedonia).
- Cambio significativo de peso o apetito.
- Insomnio o hipersomnia.
- Agitación o enlentecimiento psicomotor.
- Fatiga o pérdida de energía.
- Sentimientos de inutilidad o culpa excesiva.
- Disminución de la capacidad de pensar, concentrarse o decidir.
- Pensamientos recurrentes de muerte o ideación suicida.

## depression_persistent_dysthymia

Trastorno depresivo persistente (distimia): ánimo deprimido la mayor parte del día, casi todos los días, durante al menos 2 años (1 año en niños). Menos severo que un episodio mayor pero crónico. Funcionalmente incapacitante.

## depression_postpartum

Depresión postparto: episodio depresivo en las 4-12 semanas posteriores al parto. 10-15% de las puérperas. Diferenciar de "baby blues" (transitorio, hasta 2 semanas postparto, no requiere tratamiento). Postparto severo requiere atención inmediata: riesgo materno-infantil.

## depression_seasonal

Trastorno afectivo estacional: episodios depresivos recurrentes con patrón estacional (típicamente otoño-invierno). Tratamiento incluye fototerapia con luz brillante además de psicoterapia y eventualmente farmacoterapia.

## depression_bipolar_distinction

La depresión bipolar (fase depresiva del trastorno bipolar) requiere tratamiento distinto a depresión unipolar. Sospechar bipolar si: episodios pasados de manía o hipomanía, antecedentes familiares de bipolaridad, edad temprana de inicio, episodios depresivos recurrentes con buena respuesta inicial a antidepresivos seguida de viraje a manía. Derivar a psiquiatra para diagnóstico diferencial.

## depression_treatment_first_line

Primera línea para depresión leve-moderada: psicoterapia (CBT, IPT, psicoterapia psicodinámica de tiempo limitado). Para moderada-severa: combinación psicoterapia + farmacoterapia (ISRS típicamente).

## depression_treatment_psychotherapy_options

Psicoterapias con evidencia para depresión:

- CBT (Beck) — primera línea histórica.
- IPT (Interpersonal Therapy, Klerman) — foco en relaciones.
- Activación conductual — variante CBT.
- Psicodinámica de tiempo limitado.
- MBCT (Mindfulness-Based CBT) — específicamente prevención de recaídas en depresión recurrente.
- ACT.

## depression_treatment_pharmacotherapy

Decisión farmacológica corresponde al psiquiatra. Información NO debe darse al paciente sobre dosis ni medicamento específico desde sales_agent. Solo derivar.

## depression_treatment_combination

Para depresión moderada-severa: combinación psicoterapia + farmacoterapia es más eficaz que cada una sola. Para depresión leve: psicoterapia sola suele ser suficiente.

## depression_self_management_general_education

Manejo no clínico complementario (NO sustituye tratamiento profesional):

- Activación conductual: programar actividades placenteras y de logro a horarios fijos.
- Higiene del sueño.
- Ejercicio aeróbico regular (eficacia comparable a antidepresivos en leve-moderada).
- Exposición a luz natural matutina.
- Conexión social: contacto con vínculos significativos al menos 2-3 veces por semana.
- Reducir alcohol y consumo de sustancias.

## depression_when_to_refer_urgent

Derivación urgente:

- Ideación suicida activa con plan o intención.
- Intento previo reciente.
- Episodio depresivo severo con incapacidad funcional total.
- Síntomas psicóticos asociados (alucinaciones, delirios).
- Pérdida de peso severa o desnutrición.
- Comorbilidad con consumo de sustancias.

## depression_suicide_risk_assessment

Para evaluar riesgo suicida (lo realiza el profesional, no el sales_agent):

- Ideación: pasiva ("ojalá no despertara") vs activa ("me voy a matar").
- Plan: específico, accesible, letal.
- Intencionalidad: probabilidad de actuar.
- Factores protectores: razones para vivir, vínculos.
- Factores de riesgo: intentos previos, antecedentes familiares, aislamiento, abuso de sustancias.

Si el sales_agent detecta riesgo (palabras clave de crisis), DEBE activar `boundary_refer_out_general` + `crisis_line_<país>`.

## depression_in_children_adolescents

En niños y adolescentes: presentación atípica (irritabilidad en lugar de tristeza, somatizaciones, fracaso escolar). Riesgo suicida en adolescencia significativo. Trata profesional especializado en infancia/adolescencia.

## depression_in_elderly

En adultos mayores: presentación con quejas somáticas, deterioro cognitivo (pseudo-demencia depresiva), pérdida de interés. Diferenciar de demencia inicial, hipotiroidismo, deficiencia B12. Derivar a evaluación geriátrica integral.

## depression_treatment_resistance

Depresión resistente al tratamiento: 2+ ensayos antidepresivos con dosis y duración adecuadas sin respuesta. Manejo por psiquiatra: cambio de fármaco, potenciación, terapias de neuromodulación (TMS, TEC), nuevos agentes (ketamina). Psicoterapia continúa siempre.

## depression_relapse_prevention

Tasa de recaída alta: 50% tras primer episodio, 70% tras segundo, 90% tras tercero. Prevención de recaída: mantenimiento de tratamiento por 6-12 meses post-remisión, MBCT específicamente para prevención de recaídas, identificación de pródromos, plan escrito de afrontamiento.
