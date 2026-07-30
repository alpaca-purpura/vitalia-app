-- seed_inbox_messages.sql — dev seed: messages for the 2 Adrián inbox conversations.
-- Idempotent (fixed UUIDs + ON CONFLICT DO NOTHING). Re-runnable.
-- Tenant: Sanaré LATAM (e69a691d…) · Clinic: dr.demo's clinic (f035be5b…).
-- Conversations: 1111…(whatsapp/ai, 3 msgs) · 2222…(instagram/human, 5 msgs).
--   docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
--     -f /app/vitalia/backend/scripts/seed_inbox_messages.sql
-- story: vitalia-fase2-adrian-inbox (thread compound endpoint live-verify)

-- ── Conversation 1 (WhatsApp · Adrián decide) ─────────────────────────────────
INSERT INTO vitalia_messages
  (id, tenant_id, clinic_id, conversation_id, channel, sender_type, sender_user_id,
   body_text, handler_mode, sent_at, created_at, updated_at)
VALUES
  ('a1a1a1a1-0001-5111-8111-111111111111',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '11111111-1111-5111-8111-111111111111', 'whatsapp', 'agent_ai', NULL,
   '¡Hola! Soy Adrián, asistente de la clínica. ¿En qué puedo ayudarte?',
   'ai', now() - interval '2 days', now() - interval '2 days', now() - interval '2 days'),

  ('a1a1a1a1-0002-5111-8111-111111111111',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '11111111-1111-5111-8111-111111111111', 'whatsapp', 'patient', NULL,
   'Quiero información sobre limpieza dental.',
   'ai', now() - interval '1 day', now() - interval '1 day', now() - interval '1 day'),

  ('a1a1a1a1-0003-5111-8111-111111111111',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '11111111-1111-5111-8111-111111111111', 'whatsapp', 'patient', NULL,
   'Hola, ¿atienden los sábados para una limpieza dental?',
   'ai', now() - interval '28 minutes', now() - interval '28 minutes', now() - interval '28 minutes')
ON CONFLICT (id) DO NOTHING;

-- ── Conversation 2 (Instagram · pide humano) ──────────────────────────────────
INSERT INTO vitalia_messages
  (id, tenant_id, clinic_id, conversation_id, channel, sender_type, sender_user_id,
   body_text, handler_mode, sent_at, created_at, updated_at)
VALUES
  ('b2b2b2b2-0001-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '22222222-2222-5222-8222-222222222222', 'instagram', 'patient', NULL,
   '¡Hola! Vi su publicación sobre blanqueamiento dental.',
   'ai', now() - interval '5 days', now() - interval '5 days', now() - interval '5 days'),

  ('b2b2b2b2-0002-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '22222222-2222-5222-8222-222222222222', 'instagram', 'agent_ai', NULL,
   '¡Hola! Gracias por escribirnos. El blanqueamiento es uno de nuestros tratamientos más solicitados.',
   'ai', now() - interval '5 days' + interval '2 minutes', now() - interval '5 days', now() - interval '5 days'),

  ('b2b2b2b2-0003-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '22222222-2222-5222-8222-222222222222', 'instagram', 'agent_human', NULL,
   'Hola, soy María de la clínica. ¿Te gustaría agendar una valoración sin costo?',
   'human', now() - interval '3 days', now() - interval '3 days', now() - interval '3 days'),

  ('b2b2b2b2-0004-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '22222222-2222-5222-8222-222222222222', 'instagram', 'patient', NULL,
   'Primero quiero saber los precios, por favor.',
   'human', now() - interval '2 days', now() - interval '2 days', now() - interval '2 days'),

  ('b2b2b2b2-0005-5222-8222-222222222222',
   'e69a691d-070e-5caf-a053-6e74642ec100', 'f035be5b-0ac4-5210-8fc3-395650ca2b83',
   '22222222-2222-5222-8222-222222222222', 'instagram', 'patient', NULL,
   '¿Cuánto cuesta el blanqueamiento dental?',
   'human', now() - interval '2 hours', now() - interval '2 hours', now() - interval '2 hours')
ON CONFLICT (id) DO NOTHING;
