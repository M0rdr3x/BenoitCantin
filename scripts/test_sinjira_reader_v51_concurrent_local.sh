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


# V51.3 : deux autres courses entre catalogue et sauvegarde d'une progression.
# Un produit désactivé OU un roman dépublié pendant la sauvegarde ne doit
# pas autoriser l'écriture sous l'ancienne autorisation. Base jetable seulement.
# La fixture comprend déjà les romans fictifs 3 (publié) et 4 (annoncé).
db <<'SQL'
INSERT INTO public.user_entitlements(user_id,product_id)
VALUES ('00000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000003');
UPDATE public.sinjira_novels SET status='published'
 WHERE id='10000000-0000-0000-0000-000000000004';
SQL

make_progress() {
  local book="$1" outfile="$2"
  db -c "SET ROLE authenticated;
    SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
    SELECT result_status,result_revision,result_page
    FROM public.sinjira_reader_save_progress_cas(
     '$book',NULL,12,25,0.2000
    );" >"$outfile"
  if [[ "$(grep -E '^saved\|' "$outfile" | tail -1 || true)" != 'saved|0|12' ]]; then
    echo 'V51.3-REFUS: préparation du marque-page fictif échouée' >&2
    cat "$outfile" >&2
    exit 7
  fi
}
book3='10000000-0000-0000-0000-000000000003'
book4='10000000-0000-0000-0000-000000000004'
make_progress "$book3" "$work/progress3.output"
make_progress "$book4" "$work/progress4.output"

# Action SQL volontairement bornée à deux UPDATE prédéterminés en laboratoire;
# aucune commande de production ni identifiant externe n'est accepté.
revoke_during_save() {
  local label="$1" book="$2" statement="$3"
  local out="$work/$label.revoker.output" err="$work/$label.revoker.error"
  stdbuf -oL psql --no-psqlrc -qAt -v ON_ERROR_STOP=1 \
    -h "$HOST" -U postgres -d "$DB" >"$out" 2>"$err" <<SQL &
BEGIN;
$statement
\echo V51.3-$label-LOCK-HELD
SELECT pg_sleep(3);
COMMIT;
SQL
  local pid=$! locked=false
  for _ in $(seq 1 100); do
    if grep -Fq "V51.3-$label-LOCK-HELD" "$out" 2>/dev/null; then
      locked=true
      break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.05
  done
  if [[ "$locked" != true ]]; then
    echo "V51.3-REFUS: $label n'a pas acquis son verrou" >&2
    cat "$out" "$err" >&2
    wait "$pid" || true
    exit 8
  fi
  db -c "SET ROLE authenticated;
    SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
    SELECT result_status,result_revision,result_page
    FROM public.sinjira_reader_save_progress_cas(
      '$book',0,99,99,0.9900
    );" >"$work/$label.save.output" 2>"$work/$label.save.error"
  wait "$pid"
  local verdict
  verdict="$(grep -E '^(saved|conflict|unavailable)\|' "$work/$label.save.output" | tail -1 || true)"
  if [[ "$verdict" != 'unavailable||' ]]; then
    echo "V51.3-REFUS: $label CAS $verdict (attendu unavailable)" >&2
    cat "$work/$label.save.error" "$err" >&2
    exit 9
  fi
  echo "V51.3-$label-PASS: verrou observé, refus après modification du catalogue"
}

revoke_during_save 'PRODUCT' "$book3" \
 "UPDATE public.products SET active=false WHERE id='20000000-0000-0000-0000-000000000003';"
revoke_during_save 'NOVEL' "$book4" \
 "UPDATE public.sinjira_novels SET status='archived' WHERE id='10000000-0000-0000-0000-000000000004';"
db <<'SQL'
DO $validate$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library
  WHERE user_id='00000000-0000-0000-0000-000000000001'
    AND novel_id IN (
      '10000000-0000-0000-0000-000000000003',
      '10000000-0000-0000-0000-000000000004')
    AND last_page=12 AND revision=0;
 IF n<>2 THEN
   RAISE EXCEPTION 'V51.3: produit désactivé/roman archivé a modifié une page';
 END IF;
 SELECT count(*) INTO n FROM public.products
  WHERE id='20000000-0000-0000-0000-000000000003' AND active=false;
 IF n<>1 THEN RAISE EXCEPTION 'V51.3: produit encore actif'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_novels
  WHERE id='10000000-0000-0000-0000-000000000004' AND status='archived';
 IF n<>1 THEN RAISE EXCEPTION 'V51.3: roman encore publié'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
  WHERE user_id='00000000-0000-0000-0000-000000000002'
    AND last_page=8 AND revision=1;
 IF n<>1 THEN RAISE EXCEPTION 'V51.3: progression du compte B modifiée'; END IF;
END $validate$;
SQL
echo 'V51.3-CATALOGUE-PASS: désactivation produit et dépublication roman refusent toute sauvegarde tardive'


# V51.4 / #955 : révocation concurrente d'un rôle privilégié.
# Deux comptes entièrement fictifs : A=admin, B=owner. Les romans testés
# n'ont aucune habilitation d'achat active. Le rôle est donc le SEUL accès.
db <<'SQL'
INSERT INTO public.internal_admin_users(user_id,role) VALUES
 ('00000000-0000-0000-0000-000000000001','admin'),
 ('00000000-0000-0000-0000-000000000002','owner');
SQL

# A possède déjà un marque-page sur le livre 3, produit devenu inactif.
# B doit créer le sien sur le livre 2 (sans entitlement) avant la révocation.
db -c "SET ROLE authenticated;
 SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
 SELECT result_status,result_revision,result_page
 FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000002',NULL,14,25,0.2000
 );" >"$work/v51_4_owner_initial.output"
if [[ "$(grep -E '^saved\|' "$work/v51_4_owner_initial.output" | tail -1 || true)" != 'saved|0|14' ]]; then
 echo 'V51.4-REFUS: préparation du marque-page propriétaire' >&2
 cat "$work/v51_4_owner_initial.output" >&2
 exit 10
fi

revoke_staff_during_save() {
  local label="$1" identity="$2" book="$3"
  local log="$work/v51_4_$label.revoker.output"
  local err="$work/v51_4_$label.revoker.error"
  stdbuf -oL psql --no-psqlrc -qAt -v ON_ERROR_STOP=1 \
    -h "$HOST" -U postgres -d "$DB" >"$log" 2>"$err" <<SQL &
BEGIN;
DELETE FROM public.internal_admin_users
 WHERE user_id='$identity';
\echo V51.4-$label-ROLE-LOCK-HELD
SELECT pg_sleep(3);
COMMIT;
SQL
  local pid=$! locked=false
  for _ in $(seq 1 100); do
    if grep -Fq "V51.4-$label-ROLE-LOCK-HELD" "$log" 2>/dev/null; then
      locked=true
      break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.05
  done
  if [[ "$locked" != true ]]; then
    echo "V51.4-REFUS: $label DELETE non verrouillé" >&2
    cat "$log" "$err" >&2
    wait "$pid" || true
    exit 11
  fi
  db -c "SET ROLE authenticated;
   SET request.jwt.claim.sub='$identity';
   SELECT result_status,result_revision,result_page
   FROM public.sinjira_reader_save_progress_cas(
    '$book',0,99,99,0.9000
   );" >"$work/v51_4_$label.save.output" 2>"$work/v51_4_$label.save.error"
  wait "$pid"
  local result
  result="$(grep -E '^(saved|conflict|unavailable)\|' "$work/v51_4_$label.save.output" | tail -1 || true)"
  if [[ "$result" != 'unavailable||' ]]; then
    echo "V51.4-REFUS: $label résultat=$result, attendu unavailable" >&2
    cat "$work/v51_4_$label.save.error" "$err" >&2
    exit 12
  fi
  echo "V51.4-$label-PASS: rôle révoqué, sauvegarde concurrente refusée"
}
revoke_staff_during_save 'ADMIN' \
 '00000000-0000-0000-0000-000000000001' \
 '10000000-0000-0000-0000-000000000003'
revoke_staff_during_save 'OWNER' \
 '00000000-0000-0000-0000-000000000002' \
 '10000000-0000-0000-0000-000000000002'

db <<'SQL'
DO $roles$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.internal_admin_users;
 IF n<>0 THEN RAISE EXCEPTION 'V51.4: rôles fictifs non révoqués'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE (user_id='00000000-0000-0000-0000-000000000001'
  AND novel_id='10000000-0000-0000-0000-000000000003'
  AND last_page=12 AND revision=0)
 OR (user_id='00000000-0000-0000-0000-000000000002'
  AND novel_id='10000000-0000-0000-0000-000000000002'
  AND last_page=14 AND revision=0);
 IF n<>2 THEN RAISE EXCEPTION 'V51.4: page altérée après révocation de rôle'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000002'
   AND novel_id='10000000-0000-0000-0000-000000000001'
   AND last_page=8 AND revision=1;
 IF n<>1 THEN RAISE EXCEPTION 'V51.4: progression indépendante altérée'; END IF;
END $roles$;
SQL
echo 'V51.4-ROLE-REVOCATION-PASS: rôles admin et owner révoqués sans sauvegarde tardive ni altération'

echo 'V51-CONCURRENT-NO_GO: comptes fictifs seulement, aucune attestation production'
