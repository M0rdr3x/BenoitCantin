#!/usr/bin/env bash
# V51 : deux VRAIES connexions PostgreSQL concurrentes sur un MÊME compte fictif.
# Interdit d'utiliser une autre base, un autre hôte, Supabase ou un roman réel.
set -Eeuo pipefail
DB=sinjira_reader_v51_lab
HOST=127.0.0.1
export PGCONNECT_TIMEOUT=10
export PGOPTIONS="-c statement_timeout=30000 -c lock_timeout=20000"
db() {
  psql --no-psqlrc -qAt -v ON_ERROR_STOP=1 -h "$HOST" -U postgres -d "$DB" "$@"
}
database="$(db -c "SELECT current_database()")"
if [[ "$DB" != "sinjira_reader_v51_lab" || "$HOST" != "127.0.0.1" ||
      "$database" != "sinjira_reader_v51_lab" ]]; then
  echo 'V51-CONCURRENT-REFUS: base ou hôte hors du laboratoire jetable' >&2
  exit 3
fi
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
submit() {
  local slot="$1" page="$2"
  db -c "SET ROLE authenticated;
    SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
    SELECT result_status,result_revision,result_page
    FROM public.sinjira_reader_save_progress_cas(
     '10000000-0000-0000-0000-000000000001',2,$page,81,0.3000
    );" > "$work/$slot.output" 2>"$work/$slot.error"
}
# Après SQL V51, A est à revision 2. Les deux sessions lisent 2,
# mais l'UPDATE conditionnel ne doit en accepter qu'une seule.
submit a 51 &
pida=$!
submit b 52 &
pidb=$!
wait "$pida"
wait "$pidb"

a="$(grep -E '^(saved|conflict)\|' "$work/a.output" | tail -1)"
b="$(grep -E '^(saved|conflict)\|' "$work/b.output" | tail -1)"
if ! { [[ "$a" == saved\|3\|51 && "$b" == conflict\|3\|51 ]] ||
        [[ "$b" == saved\|3\|52 && "$a" == conflict\|3\|52 ]]; }; then
  echo "V51-CONCURRENT-REFUS: statut impossible A=$a B=$b" >&2
  cat "$work/a.error" "$work/b.error" >&2
  exit 4
fi

db <<'SQL'
DO $verify$
DECLARE page integer;rev bigint;n integer;
BEGIN
 SELECT last_page,revision INTO page,rev
 FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000001'
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF rev<>3 OR page NOT IN (51,52) THEN
  RAISE EXCEPTION 'V51-CONCURRENT: revision ou page incoherente';
 END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>3 THEN RAISE EXCEPTION 'V51-CONCURRENT: perte ou duplication de ligne'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000002'
 AND last_page=8 AND revision=1;
 IF n<>1 THEN RAISE EXCEPTION 'V51-CONCURRENT: le compte B a ete modifie'; END IF;
END $verify$;
SQL
echo 'V51-CONCURRENT-PASS: 2 sessions, 1 saved, 1 conflict, revision=3, aucune perte ni autre compte touché'
echo 'V51-CONCURRENT-NO_GO: comptes fictifs seulement, aucune attestation production'
