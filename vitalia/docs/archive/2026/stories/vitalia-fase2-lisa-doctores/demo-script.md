# Demo script — vitalia-fase2-lisa-doctores · Delta v3 (Fase G · Chris-verify)

> Cada ticket FE del delta APPENDEA su sección al cerrar (exit criterion). Stack: `make dev-vitalia` → `dev-app.vitalialat.com` (o `localhost:3002`). Usuario de prueba + tenant: ver `definition-of-done-live-verify.md § Infra por brand`.

## D3-A · Entity switcher (T-FE-switcher-wire)

1. Lisa → Staff → abrir cualquier doctor → hoja **Horarios**.
2. En la franja N3, el nombre del doctor ahora es un **selector** (avatar + nombre + ▾) — clic.
3. Se abre el buscador "Buscar integrante…" con el foco puesto; la lista muestra SOLO staff activo con ✓/resaltado en el actual (footer "Mostrando N de M").
4. Escribir parte del nombre de otro doctor → la lista filtra (server-side; ver Network: `GET /clinics/doctors?q=…&active=true` 200).
5. Elegir al otro doctor → navega a **sus Horarios** (la hoja se PRESERVA, no vuelve al directorio ni cae a Perfil) y el calendario renderiza.
6. Edge: escribir "zzqx" → "Sin resultados". Teclado: ↑↓ mueve, Enter selecciona, Esc cierra.
7. Consola: 0 errores rojos. Doctor inactivo: no aparece en la lista (sí en el directorio).

⚠️ Conocido (core, escalado): contraste del item activo (`bg-accent` púrpura sin `text-accent-foreground`) — fix 1-línea en `core/@luana/ui-kit/EntityPicker.tsx`, fuera del scope de este ticket (pin en `staff-picker-switcher.spec.ts`).

## D3-C+D3-F · Horarios — recurrencia que respeta repeticiones + editor Google (2 min)
1. Doctor → Horarios. Arrastra en una celda para crear bloque → popover.
2. Repetir → "Personalizado…": cada [2] semanas + chips L y J + "Después de [8] repeticiones".
3. Verifica el resumen: "Se repite cada 2 semanas el lunes y jueves, 8 veces". Guardar.
4. ★ EL BUG QUE REPORTASTE: navega semanas con ›. El bloque aparece SOLO en sus ocurrencias y se ACABA (antes: infinito). Crea uno "Cada semana" terminando "después de 2" → exactamente 2 semanas.
5. Los bloques muestran el patrón ("Cada 2 semanas · L, J"), no solo "Semanal".

## D3-E · Vista de MES (1 min)
6. Toggle Semana | **Mes** (arriba). Grilla mensual con chips por día + "+N más" si hay muchos.
7. Click en un día con bloques → salta a esa semana. ‹ hoy › navegan meses.

## D3-B+D3-D · Hoja "Página" — material + perfil IA + página pública (3 min)
8. Doctor → hoja **🌐 Página** (4ª pestaña — el material se mudó acá desde Perfil; en Perfil quedó una tarjeta "Ir a Página pública").
9. Sube un PDF (diploma/CV) → fila con nombre/tamaño/fecha + descargar ⬇ + eliminar ✕. (Antes el upload era un stub que NO subía nada — ahora persiste en R2/local + DB.)
10. "✨ Generar perfil" (o banner "⚡ material nuevo → Actualizar" si ya había perfil) → editor estructurado: Sobre mí · Formación · Experiencia · Tratamientos · Certificaciones · Idiomas — todo editable inline + autosave.
11. Barra superior: pill estado + **URL pública** + Copiar + Ver. El dominio es por entorno (dev-app/test-app/app .vitalialat.com).
12. Abre la URL en incógnito (o tu teléfono): página estilo Doctoralia — header sobrio + ✓ colegiatura verificada + carrera profesional. SIN botón de contacto, SIN stats. Idiomas solo si habla >1.
13. Apaga "Visible públicamente" → el link muestra "Perfil no disponible" (igual que un slug inventado — anti-enumeración).

## Switcher (30 seg — ya estaba en tu demo previa, ahora pruébalo entre hojas)
14. En Horarios de un doctor → ▾ junto al nombre → elige otro → sigues en HORARIOS del nuevo.

