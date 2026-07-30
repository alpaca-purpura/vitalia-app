# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Vitalia scheduling brand-extension module.

Inside-Out DDD layers:
  domain/       — pure Python entities, enums, dataclasses (no framework imports)
  infrastructure/ — SA 2.0 models + repositories (PhiRepositoryBase heirs)
  application/  — services + ports interfaces
  api/          — FastAPI thin routers + Pydantic DTOs
"""
