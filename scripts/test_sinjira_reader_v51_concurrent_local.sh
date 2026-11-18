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

# V51.2 / #955 : ordonnance de deux transactions distinctes.
# Transaction 1 : DELETE d'une attribution en attente de COMMIT.
# Transaction 2 : la sauvegarde CAS doit ATTENDRE et constater la révocation.
# Sans FOR SHARE, elle pourrait écrire une page après suppression du droit.
# L'essai est exécuté après les deux sauvegardes CAS concurrentes (revision=3).
revoker_log="$work/revoker.output"
revoker_err="$work/revoker.error"
# stdbuf -oL force un marqueur visible après DELETE, avant COMMIT.
stdbuf -oL psql --no-psqlrc -qAt -v ON_ERROR_STOP=1 \
  -h "$HOST" -U postgres -d "$DB" >"$revoker_log" 2>"$revoker_err" <<'SQL' &
BEGIN;
DELETE FROM public.user_entitlements
 WHERE user_id='00000000-0000-0000-0000-000000000001'
   AND product_id='20000000-0000-0000-0000-000000000001';
\echo V51-REVOKER-LOCK-HELD
SELECT pg_sleep(4);
COMMIT;
SQL
revoker_pid=$!
lock_seen=false
for _ in $(seq 1 100); do
  if grep -Fq 'V51-REVOKER-LOCK-HELD' "$revoker_log" 2>/dev/null; then
    lock_seen=true
    break
  fi
  if ! kill -0 "$revoker_pid" 2>/dev/null; then break; fi
  sleep 0.05
done
if [[ "$lock_seen" != true ]]; then
  echo 'V51.2-REFUS: révocation transactionnelle non amorcée' >&2
  cat "$revoker_log" "$revoker_err" >&2
  wait "$revoker_pid" || true
  exit 5
fi
# Le client doit lire le statut APRÈS la résolution de la transaction
# de révocation, et NON une licence issue de l'ancien snapshot.
db -c "SET ROLE authenticated;
  SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
  SELECT result_status,result_revision,result_page
  FROM public.sinjira_reader_save_progress_cas(
   '10000000-0000-0000-0000-000000000001',3,99,99,0.9900
  );" >"$work/race.output" 2>"$work/race.error"
wait "$revoker_pid"
race="$(grep -E '^(saved|conflict|unavailable)\|' "$work/race.output" | tail -1 || true)"
if [[ "$race" != 'unavailable||' ]]; then
  echo "V51.2-REFUS: sauvegarde de roman révoqué = $race" >&2
  cat "$work/race.error" "$revoker_err" >&2
  exit 6
fi
# Ni page, ni révision, ni ligne d'un autre compte ne doit changer.
db <<'SQL'
DO $verify$
DECLARE page integer;rev bigint;n integer;
BEGIN
 SELECT last_page,revision INTO page,rev
  FROM public.sinjira_reader_library
  WHERE user_id='00000000-0000-0000-0000-000000000001'
    AND novel_id='10000000-0000-0000-0000-000000000001';
 IF rev<>3 OR page NOT IN (51,52) THEN
   RAISE EXCEPTION 'V51.2: marque-page révoqué a été modifié';
 END IF;
 SELECT count(*) INTO n FROM public.user_entitlements
  WHERE user_id='00000000-0000-0000-0000-000000000001'
    AND product_id='20000000-0000-0000-0000-000000000001';
 IF n<>0 THEN
   RAISE EXCEPTION 'V51.2: suppression du droit non confirmée';
 END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
  WHERE user_id='00000000-0000-0000-0000-000000000002'
    AND last_page=8 AND revision=1;
 IF n<>1 THEN
   RAISE EXCEPTION 'V51.2: progression autre compte modifiée';
 END IF;
END $verify$;
SQL
echo 'V51.2-REVOCATION-PASS: DELETE concurrent attendue, RPC unavailable, revision=3 et compte B intacts'

echo 'V51-CONCURRENT-NO_GO: comptes fictifs seulement, aucune attestation production'
