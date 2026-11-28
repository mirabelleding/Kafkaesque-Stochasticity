BEGIN;

CREATE OR REPLACE FUNCTION public.submit_occurrences(
    p_records JSONB
)
RETURNS UUID[]
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_record JSONB;
    v_environment_id INTEGER;
    v_modality_id INTEGER;
    v_subject_id INTEGER;
    v_uuid UUID;
    v_uuids UUID[] := ARRAY[]::UUID[];
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Authentication required'
            USING ERRCODE = '42501';
    END IF;

    IF jsonb_typeof(p_records) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Records must be a JSON array';
    END IF;

    IF jsonb_array_length(p_records) = 0 THEN
        RAISE EXCEPTION 'Records cannot be empty';
    END IF;

    FOR v_record IN
        SELECT value
        FROM jsonb_array_elements(p_records) AS r(value)
    LOOP
        IF jsonb_typeof(v_record) IS DISTINCT FROM 'object' THEN
            RAISE EXCEPTION 'Each record must be an object';
        END IF;

        IF v_record ? 'created_by' OR v_record ? 'created_at' THEN
            RAISE EXCEPTION 'Creation metadata is assigned automatically';
        END IF;

        IF jsonb_typeof(v_record->'occurred_at') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'environment') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'modality') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'subject') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'testimony') IS DISTINCT FROM 'string'
            OR (
                jsonb_typeof(v_record->'ka_score') IS DISTINCT FROM 'number'
                AND (v_record->>'ka_score') IS DISTINCT FROM 'inf'
            )
        THEN
            RAISE EXCEPTION 'Missing or invalid required field';
        END IF;

        IF (v_record->>'occurred_at') !~
            '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?$'
        THEN
            RAISE EXCEPTION 'occurred_at must be a timestamp without timezone';
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
            subject_id
        )
        VALUES (
            (v_record->>'occurred_at')::TIMESTAMP,
            v_environment_id,
            v_modality_id,
            (v_record->>'ka_score')::NUMERIC,
            v_subject_id
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


CREATE OR REPLACE FUNCTION public.submit_presence(
    p_records JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_record JSONB;
    v_subject_id INTEGER;
    v_start TIMESTAMP;
    v_end TIMESTAMP;
    v_timestamp_pattern CONSTANT TEXT :=
        '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?$';
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Authentication required'
            USING ERRCODE = '42501';
    END IF;

    IF jsonb_typeof(p_records) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Records must be a JSON array';
    END IF;

    IF jsonb_array_length(p_records) = 0 THEN
        RAISE EXCEPTION 'Records cannot be empty';
    END IF;

    FOR v_record IN
        SELECT value
        FROM jsonb_array_elements(p_records) AS r(value)
    LOOP
        IF jsonb_typeof(v_record) IS DISTINCT FROM 'object' THEN
            RAISE EXCEPTION 'Each record must be an object';
        END IF;

        IF v_record ? 'created_by' OR v_record ? 'created_at' THEN
            RAISE EXCEPTION 'Creation metadata is assigned automatically';
        END IF;

        IF jsonb_typeof(v_record->'subject') IS DISTINCT FROM 'string'
            OR jsonb_typeof(v_record->'start') IS DISTINCT FROM 'string'
            OR (
                jsonb_typeof(v_record->'end') IS DISTINCT FROM 'string'
                AND jsonb_typeof(v_record->'end') IS DISTINCT FROM 'null'
            )
        THEN
            RAISE EXCEPTION 'Missing or invalid required field';
        END IF;

        IF (v_record->>'start') !~ v_timestamp_pattern
            OR (v_record->>'end') !~ v_timestamp_pattern
        THEN
            RAISE EXCEPTION 'Timestamps must be without timezone';
        END IF;

        v_start := (v_record->>'start')::TIMESTAMP;
        v_end := (v_record->>'end')::TIMESTAMP;

        IF v_end IS NOT NULL AND v_start >= v_end THEN
            RAISE EXCEPTION 'Presence start must precede end';
        END IF;

        SELECT id INTO v_subject_id
        FROM public.subjects
        WHERE name = v_record->>'subject';

        IF v_subject_id IS NULL THEN
            RAISE EXCEPTION 'Unknown subject: %',
                v_record->>'subject';
        END IF;

        INSERT INTO public.presences (
            subject_id,
            presence_interval
        )
        VALUES (
            v_subject_id,
            tsrange(v_start, v_end, '[]')
        );
    END LOOP;

    RETURN jsonb_array_length(p_records);
END;
$$;


REVOKE ALL ON FUNCTION
    public.submit_occurrences(JSONB),
    public.submit_presence(JSONB)
FROM PUBLIC, anon, authenticated;

COMMIT;