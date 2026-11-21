BEGIN;

DROP FUNCTION IF EXISTS public.submit_occurrences(JSONB, UUID);

CREATE OR REPLACE FUNCTION public.submit_occurrences(
    p_records JSONB
)
RETURNS UUID[]
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_user_id UUID := auth.uid();
    v_record JSONB;
    v_environment_id INTEGER;
    v_modality_id INTEGER;
    v_subject_id INTEGER;
    v_uuid UUID;
    v_uuids UUID[] := ARRAY[]::UUID[];
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required'
            USING ERRCODE = '42501';
    END IF;

    IF jsonb_typeof(p_records) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Records must be a JSON array';
    END IF;

    IF jsonb_array_length(p_records) NOT BETWEEN 1 AND 500 THEN
        RAISE EXCEPTION 'Batch must contain between 1 and 500 records';
    END IF;

    FOR v_record IN
        SELECT value
        FROM jsonb_array_elements(p_records) AS r(value)
    LOOP
        IF jsonb_typeof(v_record) IS DISTINCT FROM 'object' THEN
            RAISE EXCEPTION 'Each record must be an object';
        END IF;

        IF v_record ? 'project' THEN
            RAISE EXCEPTION 'Use environment instead of project';
        END IF;

        IF v_record ? 'context' THEN
            RAISE EXCEPTION 'Use modality instead of context';
        END IF;

        IF v_record ? 'contributor_id' THEN
            RAISE EXCEPTION 'contributor_id is assigned automatically';
        END IF;

        IF jsonb_typeof(v_record->'occurred_at') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'environment') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'modality') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'subject') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'testimony') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'ka_score') IS DISTINCT FROM 'number'
        THEN
            RAISE EXCEPTION 'Missing or invalid required field';
        END IF;

        IF (v_record->>'occurred_at') !~
            '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?$'
        THEN
            RAISE EXCEPTION 'occurred_at must be a timestamp without timezone';
        END IF;

        IF (v_record->>'ka_score') !~ '^-?[0-9]+$' THEN
            RAISE EXCEPTION 'ka_score must be an integer';
        END IF;

        IF btrim(v_record->>'testimony') = '' THEN
            RAISE EXCEPTION 'Testimony cannot be empty';
        END IF;

        SELECT id INTO v_environment_id
        FROM public.environments
        WHERE name = v_record->>'environment';

        IF v_environment_id IS NULL THEN
            RAISE EXCEPTION 'Unknown environment: %',
                v_record->>'environment';
        END IF;

        SELECT id INTO v_modality_id
        FROM public.modalities
        WHERE name = v_record->>'modality';

        IF v_modality_id IS NULL THEN
            RAISE EXCEPTION 'Unknown modality: %',
                v_record->>'modality';
        END IF;

        SELECT id INTO v_subject_id
        FROM public.subjects
        WHERE name = v_record->>'subject';

        IF v_subject_id IS NULL THEN
            RAISE EXCEPTION 'Unknown subject: %',
                v_record->>'subject';
        END IF;

        INSERT INTO public.occurrences (
            occurred_at,
            environment_id,
            modality_id,
            ka_score,
            subject_id,
            contributor_id
        )
        VALUES (
            (v_record->>'occurred_at')::TIMESTAMP,
            v_environment_id,
            v_modality_id,
            (v_record->>'ka_score')::SMALLINT,
            v_subject_id,
            v_user_id
        )
        RETURNING uuid INTO v_uuid;

        INSERT INTO public.testimonies (
            occurrence_id,
            testimony
        )
        VALUES (
            v_uuid,
            v_record->>'testimony'
        );

        v_uuids := array_append(v_uuids, v_uuid);
    END LOOP;

    RETURN v_uuids;
END;
$$;

REVOKE ALL ON TABLE public.occurrences, public.testimonies
FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.occurrences, public.testimonies
TO authenticated;

REVOKE ALL ON FUNCTION public.submit_occurrences(JSONB)
FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.submit_occurrences(JSONB)
TO authenticated;

COMMIT;
