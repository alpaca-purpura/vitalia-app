# P2 · DevHub — Visión de producto

> Célula estanca (I-69). Visión que evoluciona independiente según mercado y clientes.
> Registro: [`LEDGER.md`](./LEDGER.md) (`DH-NN`). Ecosistema: `tooling/strategy/PRODUCT-VISION.md`.

## Identidad

Sistema **completamente independiente** de gestión del desarrollo: visualización y gestión de **todo el ciclo de vida del software**. Premisa de mercado: una empresa no tiene un solo sistema, y un programador toca varios — el producto es multi-sistema y multi-proyecto por diseño.

**Nivel de ingeniería alto** en lo que toca al código: manejo de **ramas, repositorios y control de versiones**. Próximamente: vista de **pases a producción (releases)**.

## Roles / control de accesos

- **CEO / Líder técnico** — vista global: todos los sistemas, proyectos y avances de la empresa.
- **Desarrollador** — vista restringida: solo sus proyectos; incluso limitada a los módulos o repositorios específicos asignados.
- Evolución: **CTO · líder · programador · devops** como roles de primera clase.

## Interconexiones (ecosistema)

- Corre **de la mano del Kit** (P3): las piezas del kit ("las carnes") se **visualizan y gestionan aquí**. Probablemente un kit por rol (lo definirá P3).
- **P1 (Cockpit)** puede extraer las capabilities de este sistema si el cliente tiene ambos — sistemas separados, contrato de lectura.
- La telemetría que emite el Kit (I-53) alimenta a P4.

## Estado (checkpoint — 2026-07-01)

- **Maduro como visor**: board 10 estados · roadmap · mapa (2 lentes) · drift · learnings · CIL/harness board · multi-workspace · SSE · deep-links · nav per-board. Go con paridad 18/18 endpoints; UI v0.6.0.
- **Gap contra la visión**: gestión real de ramas/repos/versiones · vista de releases · roles/accesos (hoy no hay auth) · el rename comercial (binario/CLI se llaman `cockpit`).
- **Siguiente:** sesión de célula — roadmap DH desde los gaps + TBDs del grill.

## TBD — pendientes del grill

- **Comprador con nombre** (¿CTO de software factory? ¿líder de equipo AI-native?) · **pricing** · **éxito a 12m**.
- **Rebanada de servicio** (¿implantación + training del proceso?).
- **JTBD + historias** del norte.

## Gestión

Backlog vivo: sistema en el cockpit del operador (dogfood: DevHub se gestiona con DevHub).
