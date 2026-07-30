-- seed_inbox_conversations.sql — dev seed for Adrián inbox (Sanaré tenant).
-- Idempotent (fixed UUIDs + ON CONFLICT DO NOTHING). Re-runnable.
-- Tenant: Sanaré LATAM (e69a691d…) · Clinic: dr.demo's clinic (f035be5b…).
-- Conversations link to existing vitalia_leads. Commercial inbox data (non-PHI previews).
--   docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
--     -f /app/vitalia/backend/scripts/seed_inbox_conversations.sql
-- story: vitalia-fase2-adrian-inbox (un-stub list + seed for live-verify)

INSERT INTO vitalia_conversations
  (id, tenant_id, clinic_id, lead_id, channel, status, handler_mode,
   proposal_required, help_needed, help_needed_reason, unread_media_count,
   last_message_at, last_message_preview, messages_count, stage_decision,
   created_at, updated_at)
VALUES
  ('11111111-1111-5111-8111-111111111111',
   'e69a691d-070e-5caf-a053-6e74642ec100',
   'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '66afe78e-968b-545c-9454-449da3d7e66d',
   'whatsapp', 'open', 'ai',
   false, false, NULL, 0,
   now() - interval '28 minutes',
   'Hola, ¿atienden los sábados para una limpieza dental?',
   3, 'interesado',
   now() - interval '2 days', now() - interval '28 minutes'),

  ('22222222-2222-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100',
   'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   'ee614d76-3471-4fe2-9f85-4b1230f69381',
   'instagram', 'open', 'human',
   false, true, 'El paciente pide hablar con una persona', 1,
   now() - interval '2 hours',
   '¿Cuánto cuesta el blanqueamiento dental?',
   5, 'calificando',
   now() - interval '5 days', now() - interval '2 hours')
ON CONFLICT (id) DO NOTHING;
