<!-- AUTO-GENERATED via make infra-matrix — DO NOT EDIT MANUALLY -->

# INFRA-MATRIX — Puertos, dominios y databases por brand

> Generado automaticamente por `make infra-matrix`. SSoT: `{brand}/config/brand.yaml::infra`. NO editar manualmente.

## Entorno dev local

| Brand | Backend port | Frontend port | DB name | Redis DB | Qdrant prefix | Dev domain |
|---|---|---|---|---|---|---|
| comunify | 8003 | 3003 | comunify_dev | 2 | comunify_ | comunify-dev.nicolify.com |
| fitflow | 8010 | 3010 | fitflow_dev | 9 | fitflow_ | fitflow-dev.nicolify.com |
| fixia | 8008 | 3008 | fixia_dev | 7 | fixia_ | fixia-dev.nicolify.com |
| guestly | 8009 | 3009 | guestly_dev | 8 | guestly_ | guestly-dev.nicolify.com |
| inmoflow | 8006 | 3006 | inmoflow_dev | 5 | inmoflow_ | inmoflow-dev.nicolify.com |
| lupulo | 8004 | 3004 | lupulo_dev | 3 | lupulo_ | lupulo-dev.nicolify.com |
| nicolify | 8001 | 3001 | nicolify_dev | 0 | nicolify_ | nicolify-dev.nicolify.com |
| retailly | 8007 | 3007 | retailly_dev | 6 | retailly_ | retailly-dev.nicolify.com |
| saasora | 8005 | 3005 | saasora_dev | 4 | saasora_ | saasora-dev.nicolify.com |
| vitalia | 8002 | 3002 | vitalia_dev | 1 | vitalia_ | vitalia-dev.nicolify.com |

## Entorno produccion

| Brand | Prod domain | Servidor |
|---|---|---|
| comunify | app.comunify.com | tbd |
| fitflow | app.fitflow.com | tbd |
| fixia | app.fixia.com | tbd |
| guestly | app.guestly.com | tbd |
| inmoflow | app.inmoflow.com | tbd |
| lupulo | app.lupulo.com | tbd |
| nicolify | app.nicolify.com | tbd |
| retailly | app.retailly.com | tbd |
| saasora | app.saasora.com | tbd |
| vitalia | app.vitalialat.com | tbd |

## Puertos compartidos (shared infra)

| Servicio | Host port | Container port | Notas |
|---|---|---|---|
| postgres | 5435 | 5432 | Shared — 1 instancia, N databases (D1) |
| qdrant | 6333/6334 | 6333/6334 | Opt-in profile `vector` (D3) |
| redis | 6379 | 6379 | Opt-in profile `cache` (D3) |
