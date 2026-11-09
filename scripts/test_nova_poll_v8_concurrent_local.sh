#!/usr/bin/env bash
# Projet Nova V8: essai concurrent sur PostgreSQL 17.6 JETABLE, local exclusivement.
# AUCUN vrai participant, aucune origine Supabase, aucun secret, aucun vote réel.
set -Eeuo pipefail

DB="nova_poll_v7_disposable"
HOST="127.0.0.1"
PGUSER="postgres"
export PGCONNECT_TIMEOUT=10
export PGOPTIONS="-c statement_timeout=30000 -c lock_timeout=20000"

db() {
  command psql --no-psqlrc -qAt -v ON_ERROR_STOP=1 -h "$HOST" -U "$PGUSER" -d "$DB" "$@"
}

# Contrôler l'identité du serveur AVANT toute commande qui modifie des lignes.
actual="$(db -c "SELECT current_database()||':'||host(inet_server_addr())")"
if [[ "$actual" != "nova_poll_v7_disposable:127.0.0.1" ]]; then
  echo "NOVA-V8-REFUS: serveur ou base non fictifs ($actual)" >&2
  exit 10
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
answers='{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'

reset_fixture() {
  # Uniquement dans la base dont l'identité a été vérifiée plus haut.
  db <<'SQL'
TRUNCATE public.nova_poll_counts, public.nova_poll_receipts, public.nova_poll_public_counts;
UPDATE public.nova_poll_publication_state
SET published_ballots=0,published_at=NULL WHERE poll_version='nova-consultation-v1';
SQL
}
submit_fake() {
  local label="$1" token="$2"
  # Connexions psql distinctes : Postgres tranche atomiquement par UNIQUE.
  db -c "SET ROLE service_role; SELECT public.nova_poll_submit(
    'nova-consultation-v1','$token','$answers'::jsonb
  )" > "$work/$label.result" 2> "$work/$label.error"
}

check_output() {
  local label="$1" expected="$2"
  if [[ "$(cat "$work/$label.result")" != "$expected" ]]; then
    echo "NOVA-V8-REFUS: $label = $(cat "$work/$label.result") (attendu $expected)" >&2
    cat "$work/$label.error" >&2
    exit 12
  fi
}

# CAS 1 : le MÊME jeton envoyé dans deux sessions physiques concurrentes.
reset_fixture
token="$(printf '%064x' 777)"
submit_fake duplicate_1 "$token" &
pid1=$!
submit_fake duplicate_2 "$token" &
pid2=$!
wait "$pid1"
wait "$pid2"
one="$(cat "$work/duplicate_1.result")"
two="$(cat "$work/duplicate_2.result")"
if ! { [[ "$one" == "accepted" && "$two" == "duplicate" ]] ||
        [[ "$two" == "accepted" && "$one" == "duplicate" ]]; }; then
  echo "NOVA-V8-REFUS: deux soumissions simultanées du même jeton ($one, $two)" >&2
  exit 13
fi
db <<'SQL'
DO $verify$
BEGIN
 IF (SELECT count(*) FROM public.nova_poll_receipts)<>1
 OR (SELECT count(*) FROM public.nova_poll_counts)<>8
 OR (SELECT COALESCE(sum(total),0) FROM public.nova_poll_counts)<>8
 OR (SELECT published_ballots FROM public.nova_poll_publication_state
     WHERE poll_version='nova-consultation-v1')<>0
 THEN
   RAISE EXCEPTION 'NOVA-V8: double comptage ou publication avant seuil';
 END IF;
END $verify$;
SQL
echo "NOVA-V8-CONCURRENT-DUPLICATE-PASS: 2 connexions, 1 acceptée, 1 doublon, 8 agrégats"

# CAS 2 : 16 connexions indépendantes, chacune un jeton FICTIF distinct.
# Elles sont lancées sans attendre les autres. Une erreur ou un deadlock échoue CI.
reset_fixture
pids=""
for i in $(seq 1 16); do
  token="$(printf '%064x' "$i")"
  submit_fake "unique_$i" "$token" &
  pids="$pids $!"
done
for p in $pids; do
  wait "$p"
done
for i in $(seq 1 16); do
  check_output "unique_$i" "accepted"
done
db <<'SQL'
DO $verify$
DECLARE n bigint; published bigint; published_rows integer;
BEGIN
 SELECT count(*) INTO n FROM public.nova_poll_receipts;
 IF n<>16 THEN RAISE EXCEPTION 'NOVA-V8: % reçus et non 16',n; END IF;
 SELECT count(*) INTO n FROM public.nova_poll_counts
 WHERE poll_version='nova-consultation-v1' AND option_value=-2 AND total=16;
 IF n<>8 THEN RAISE EXCEPTION 'NOVA-V8: 8 compteurs attendus à 16, obtenu %',n; END IF;
 SELECT count(*) INTO n FROM public.nova_poll_counts;
 IF n<>8 THEN RAISE EXCEPTION 'NOVA-V8: catégorie indue ou double comptage'; END IF;
 SELECT published_ballots INTO published
 FROM public.nova_poll_publication_state WHERE poll_version='nova-consultation-v1';
 IF published<10 OR published>16 THEN
   RAISE EXCEPTION 'NOVA-V8: publication hors seuil, %',published;
 END IF;
 SELECT count(*) INTO published_rows FROM public.nova_poll_public_counts
 WHERE poll_version='nova-consultation-v1' AND option_value=-2 AND total=published;
 IF published_rows<>8 THEN
   RAISE EXCEPTION 'NOVA-V8: 8 instantanés agrégés incohérents (%).',published_rows;
 END IF;
END $verify$;
SQL
echo "NOVA-V8-CONCURRENT-UNIQUE-PASS: 16 connexions, 16 reçus, 8 compteurs cohérents"
echo "NOVA-V8-LAB-ONLY-NO_GO: essai SQL local ≠ CAPTCHA, droits ni autorisation de vote en production"
