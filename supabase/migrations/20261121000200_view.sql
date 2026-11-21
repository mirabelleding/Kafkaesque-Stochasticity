BEGIN;

CREATE OR REPLACE VIEW public.k_occurrences_v
WITH (security_invoker = true)
AS
SELECT
    o.uuid,
    o.occurred_at,
    o.environment_id,
    e.name AS environment,
    o.modality_id,
    m.name AS modality,
    o.ka_score,
    o.subject_id,
    s.name AS subject,
    o.contributor_id,
    t.testimony
FROM public.occurrences AS o
LEFT JOIN public.environments AS e ON o.environment_id = e.id
JOIN public.modalities AS m ON o.modality_id = m.id
JOIN public.subjects AS s ON o.subject_id = s.id
LEFT JOIN public.testimonies AS t ON o.uuid = t.occurrence_id;

REVOKE ALL ON public.k_occurrences_v
FROM PUBLIC, anon, authenticated;

GRANT SELECT ON public.k_occurrences_v TO authenticated;

COMMIT;
