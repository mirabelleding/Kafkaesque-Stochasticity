BEGIN;

DO $$
DECLARE
    v_role TEXT;
BEGIN
    FOREACH v_role IN ARRAY ARRAY['admin', 'contributor']
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_roles
            WHERE rolname = v_role
        ) THEN
            EXECUTE format('CREATE ROLE %I NOLOGIN INHERIT', v_role);
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_roles
            WHERE rolname = v_role
                AND (rolcanlogin OR NOT rolinherit OR rolsuper
                     OR rolcreaterole OR rolcreatedb OR rolreplication
                     OR rolbypassrls)
        ) THEN
            RAISE EXCEPTION 'Unexpected attributes for role: %', v_role;
        END IF;
    END LOOP;
END;
$$;

GRANT contributor TO admin;

CREATE SCHEMA IF NOT EXISTS private;

CREATE TABLE private.login_identities (
    username NAME PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE
        REFERENCES auth.users(id) ON DELETE CASCADE
);

REVOKE ALL ON SCHEMA private
FROM PUBLIC, anon, authenticated, contributor, admin;

REVOKE ALL ON TABLE private.login_identities
FROM PUBLIC, anon, authenticated, contributor, admin;

CREATE OR REPLACE FUNCTION private.actor_id()
RETURNS UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT CASE
        WHEN session_user = 'authenticator'
            THEN auth.uid()
        ELSE (
            SELECT user_id
            FROM private.login_identities
            WHERE username = session_user
        )
    END;
$$;

CREATE OR REPLACE FUNCTION private.actor_role()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT CASE
        WHEN private.actor_id() IS NULL
            THEN NULL
        WHEN session_user = 'authenticator'
            THEN auth.jwt() -> 'app_metadata' ->> 'role'
        WHEN pg_has_role(session_user, 'admin', 'MEMBER')
            THEN 'admin'
        WHEN pg_has_role(session_user, 'contributor', 'MEMBER')
            THEN 'contributor'
        ELSE NULL
    END;
$$;

REVOKE ALL ON FUNCTION
    private.actor_id(),
    private.actor_role()
FROM PUBLIC, anon, authenticated, contributor, admin;

GRANT EXECUTE ON FUNCTION
    private.actor_id(),
    private.actor_role()
TO authenticated, contributor, admin;

GRANT CONNECT ON DATABASE postgres
TO contributor, admin;

REVOKE CREATE ON SCHEMA public
FROM PUBLIC, anon, authenticated, contributor, admin;

GRANT USAGE ON SCHEMA public, private
TO authenticated, contributor, admin;

REVOKE ALL ON TABLE
    public.environments,
    public.modalities,
    public.subjects,
    public.subject_presence,
    public.occurrences,
    public.testimonies,
    public.k_occurrences_v,
    public.k_presence_v
FROM PUBLIC, anon, authenticated, contributor, admin;

GRANT SELECT ON TABLE
    public.environments,
    public.modalities,
    public.subjects,
    public.subject_presence,
    public.occurrences,
    public.testimonies,
    public.k_occurrences_v,
    public.k_presence_v
TO authenticated, contributor, admin;

GRANT INSERT (name), UPDATE (name) ON TABLE
    public.environments,
    public.modalities,
    public.subjects
TO authenticated, admin;

GRANT INSERT (subject_id, presence_interval),
      UPDATE (subject_id, presence_interval)
ON TABLE public.subject_presence
TO authenticated, admin;

GRANT INSERT (
    occurred_at,
    environment_id,
    modality_id,
    ka_score,
    subject_id
), UPDATE (
    occurred_at,
    environment_id,
    modality_id,
    ka_score,
    subject_id
)
ON TABLE public.occurrences
TO authenticated, contributor, admin;

GRANT INSERT (occurrence_id, testimony), UPDATE (testimony)
ON TABLE public.testimonies
TO authenticated, contributor, admin;

GRANT DELETE ON TABLE
    public.environments,
    public.modalities,
    public.subjects,
    public.subject_presence,
    public.occurrences,
    public.testimonies
TO authenticated, admin;

DO $$
DECLARE
    v_table TEXT;
BEGIN
    FOREACH v_table IN ARRAY ARRAY[
        'environments',
        'modalities',
        'subjects',
        'subject_presence',
        'occurrences'
    ]
    LOOP
        EXECUTE format(
            'ALTER TABLE public.%I
                ALTER COLUMN created_by
                SET DEFAULT private.actor_id()',
            v_table
        );
    END LOOP;
END;
$$;

DO $$
DECLARE
    v_table TEXT;
BEGIN
    FOREACH v_table IN ARRAY ARRAY[
        'environments',
        'modalities',
        'subjects',
        'subject_presence',
        'occurrences',
        'testimonies'
    ]
    LOOP
        EXECUTE format(
            'CREATE POLICY admin_all
                ON public.%I
                FOR ALL TO authenticated, admin
                USING ((SELECT private.actor_role()) = ''admin'')
                WITH CHECK ((SELECT private.actor_role()) = ''admin'')',
            v_table
        );
    END LOOP;
END;
$$;

DO $$
DECLARE
    v_table TEXT;
BEGIN
    FOREACH v_table IN ARRAY ARRAY[
        'environments',
        'modalities',
        'subjects',
        'subject_presence'
    ]
    LOOP
        EXECUTE format(
            'CREATE POLICY contributor_select
                ON public.%I
                FOR SELECT TO authenticated, contributor
                USING ((SELECT private.actor_role()) = ''contributor'')',
            v_table
        );
    END LOOP;
END;
$$;

CREATE POLICY contributor_select
    ON public.occurrences
    FOR SELECT TO authenticated, contributor
    USING (
        (SELECT private.actor_role()) = 'contributor'
        AND created_by = (SELECT private.actor_id())
    );

CREATE POLICY contributor_insert
    ON public.occurrences
    FOR INSERT TO authenticated, contributor
    WITH CHECK (
        (SELECT private.actor_role()) = 'contributor'
        AND created_by = (SELECT private.actor_id())
    );

CREATE POLICY contributor_update
    ON public.occurrences
    FOR UPDATE TO authenticated, contributor
    USING (
        (SELECT private.actor_role()) = 'contributor'
        AND created_by = (SELECT private.actor_id())
    )
    WITH CHECK (
        (SELECT private.actor_role()) = 'contributor'
        AND created_by = (SELECT private.actor_id())
    );

CREATE POLICY contributor_select
    ON public.testimonies
    FOR SELECT TO authenticated, contributor
    USING (
        (SELECT private.actor_role()) = 'contributor'
        AND EXISTS (
            SELECT 1
            FROM public.occurrences AS o
            WHERE o.uuid = testimonies.occurrence_id
                AND o.created_by = (SELECT private.actor_id())
        )
    );

CREATE POLICY contributor_insert
    ON public.testimonies
    FOR INSERT TO authenticated, contributor
    WITH CHECK (
        (SELECT private.actor_role()) = 'contributor'
        AND EXISTS (
            SELECT 1
            FROM public.occurrences AS o
            WHERE o.uuid = testimonies.occurrence_id
                AND o.created_by = (SELECT private.actor_id())
        )
    );

CREATE POLICY contributor_update
    ON public.testimonies
    FOR UPDATE TO authenticated, contributor
    USING (
        (SELECT private.actor_role()) = 'contributor'
        AND EXISTS (
            SELECT 1
            FROM public.occurrences AS o
            WHERE o.uuid = testimonies.occurrence_id
                AND o.created_by = (SELECT private.actor_id())
        )
    )
    WITH CHECK (
        (SELECT private.actor_role()) = 'contributor'
        AND EXISTS (
            SELECT 1
            FROM public.occurrences AS o
            WHERE o.uuid = testimonies.occurrence_id
                AND o.created_by = (SELECT private.actor_id())
        )
    );

REVOKE ALL ON FUNCTION
    public.submit_occurrences(JSONB),
    public.submit_presence(JSONB)
FROM PUBLIC, anon, authenticated, contributor, admin;

GRANT EXECUTE ON FUNCTION
    public.submit_occurrences(JSONB),
    public.submit_presence(JSONB)
TO authenticated;

COMMIT;