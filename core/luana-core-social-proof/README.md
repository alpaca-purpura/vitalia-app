# luana-core-social-proof

Brand-agnostic social proof management package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/social_proof/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/social_proof/`.

## Key exports

- `luana_core_social_proof.domain.testimonial.Testimonial` — testimonial aggregate
- `luana_core_social_proof.domain.authority_item.AuthorityItem` — authority aggregate
- `luana_core_social_proof.domain.team_member.TeamMember` — team member aggregate
- `luana_core_social_proof.domain.placement.Placement` — placement aggregate
- `luana_core_social_proof.infrastructure.repositories` — repository implementations
- `luana_core_social_proof.api.{testimonials,authority,team_members,placements}` — FastAPI routers
- `luana_core_social_proof.application.services.social_proof_resolver.SocialProofResolver`

## Deferred

- `copilot_provider/` — deferred to Story 6 (copilot lift). Imports `copilot.domain.ports`.

## Version

0.0.1-alpha (Story 3 lift)
