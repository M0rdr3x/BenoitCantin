#!/usr/bin/env bash
set -euo pipefail
# Exécuter UNIQUEMENT dans la base fictive d'un service PostgreSQL CI.
if [[ "$PGHOST" != "127.0.0.1" || "$PGDATABASE" != "sinjira_test" ]]; then
  echo "REFUS: ce test ne doit jamais viser une base Supabase réelle." >&2
  exit 1
fi
ADMIN="aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
REPORT="dddddddd-dddd-4ddd-dddd-ddddddddddd3"
FIRST="BEGIN; select set_config('request.jwt.claims','{\"role\":\"service_role\"}',false); set role service_role; select public.sinjira_admin_moderate_atomic('$ADMIN','$REPORT','hide_content','Règles communautaires de sécurité','Première décision humaine sur le signalement concurrent.','standard',null); select pg_sleep(2); COMMIT;"
SECOND="BEGIN; select set_config('request.jwt.claims','{\"role\":\"service_role\"}',false); set role service_role; select public.sinjira_admin_moderate_atomic('$ADMIN','$REPORT','hide_content','Règles communautaires de sécurité','Deuxième décision qui doit être rejetée sous verrou concurrent.','standard',null); COMMIT;"
first_log="$(mktemp)"
second_log="$(mktemp)"
trap 'rm -f "$first_log" "$second_log"' EXIT
psql -v ON_ERROR_STOP=1 -c "$FIRST" >"$first_log" 2>&1 &
first_pid=$!
sleep 0.6
set +e
psql -v ON_ERROR_STOP=1 -c "$SECOND" >"$second_log" 2>&1
second_code=$?
wait "$first_pid"
first_code=$?
set -e
if [[ "$first_code" -ne 0 || "$second_code" -eq 0 ]] || ! grep -q 'REPORT_NOT_OPEN' "$second_log"; then
  echo "ECHEC : une seule transaction doit réussir sur le même signalement." >&2
  exit 1
fi
number="$(psql -Atv ON_ERROR_STOP=1 -c "select count(*) from private.moderation_decisions where report_id='$REPORT'")"
state="$(psql -Atv ON_ERROR_STOP=1 -c "select status from public.social_reports where id='$REPORT'")"
if [[ "$number" != "1" || "$state" != "resolved" ]]; then
  echo "ECHEC : anomalie de cohérence de rapport après concurrence." >&2
  exit 1
fi
echo "PASS : deux administrateurs fictifs simultanés, une seule décision atomique."
