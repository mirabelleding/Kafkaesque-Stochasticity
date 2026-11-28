#!/usr/bin/env bash

set -euo pipefail

supabase db reset --local --no-seed

eval "$(supabase status -o env | grep '^SERVICE_ROLE_KEY=')"

curl --fail-with-body -sS \
    -X POST "http://127.0.0.1:54321/auth/v1/admin/users" \
    -H "apikey: $SERVICE_ROLE_KEY" \
    -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "test123",
        "email_confirm": true,
        "app_metadata": {"role": "admin"}
    }'

printf '\nLocal admin user created successfully.\nEmail: test@test.com\nPassword: test123\n'