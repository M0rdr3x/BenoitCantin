#!/usr/bin/env node
// Inventaire G0–G4, totalement local et en lecture seule. AUCUNE homologation.
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import {auditerReceptionG0} from "../assets/nova-sinjira-g0-reception-core.mjs";
const input=fileURLToPath(new URL("../data/registre-donnees-services-nova-sinjira.json",import.meta.url));
const raw=JSON.parse(await readFile(input,"utf8"));
const report=auditerReceptionG0(raw);
const output={
 schema:"nova-sinjira-g0-readonly-inventory/v1",
 statut:"REVUE_INTERNE_NON_CERTIFICATIVE",
 date_du_registre:report.reference_registry_date,
 total_secteurs:report.nb_secteurs,
 candidats_diagnostic_G0:report.dossiers_avec_base_documentee_pour_revue,
 candidats_comparaison_G1:report.dossiers_avec_couts_candidats_pour_revue,
 G0_independamment_atteste:report.g0_independamment_atteste,
 pilotes_autorises:report.g3_pilotes_autorises,
 taux_achevement_global:report.taux_global_completion,
 phase_adoption_autorisee:report.pret_a_deployer,
 alertes:report.anomalies,
 dossiers:report.dossiers.map(d=>({
  id:d.id,nom:d.domaine,
  indicateur_propose:d.indicateur_propose,
  source_partielle_non_financiere:d.source_documentaire_partielle_declared,
  champs_g0_manquants:d.champs_baseline_manquants,
  couts_comparables_non_demontres:d.comparateurs_couts_complets_manquants,
  recevable_pour_revue_g0:d.g0_candidat_pour_revue_humaine,
  porte_g0_attestee:d.g0_reception_officielle,
  pilote_autorise:d.g3_pilote_autorise,
  action:d.prochaine_action
 }))
};
process.stdout.write(JSON.stringify(output,null,2)+"\n");
if(!report.ok)process.exitCode=1;
