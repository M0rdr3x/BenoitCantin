import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const data=JSON.parse(await readFile(new URL("../data/registre-donnees-services-nova-sinjira.json",import.meta.url),"utf8"));
const financial=JSON.parse(await readFile(new URL("../data/reperes-financiers-nova-sinjira-2026.json",import.meta.url),"utf8"));
const ids=data.dossiers.map(x=>x.id);

test("le registre couvre exactement les 14 portefeuilles distincts",()=>{
  assert.equal(data.dossiers.length,14);
  assert.equal(new Set(ids).size,14);
  assert.deepEqual(ids,Array.from({length:14},(_,i)=>"NV-"+String(i+1).padStart(2,"0")));
});
test("chaque dossier documente les sources et garde les coûts inconnus",()=>{
  for(const d of data.dossiers){
    assert.ok(d.domaine && d.unite_comparaison_proposee && d.indicateurs_proposes);
    assert.ok(Array.isArray(d.sources_institutionnelles_possibles));
    assert.ok(d.sources_institutionnelles_possibles.length>0);
    assert.equal(d.chiffrage_valide,false);
    assert.equal(d.nombre_unites,null);
    assert.equal(d.date_valeur,null);
    assert.equal(d.qualite_verifiee,false);
    assert.equal(d.couts_par_mode.public_actuel,null);
    assert.equal(d.couts_par_mode.public_reorganise,null);
    assert.equal(d.couts_par_mode.prive,null);
    assert.equal(d.couts_par_mode.cooperative,null);
    assert.equal(d.couts_par_mode.obnl,null);
  }
});
test("les repères budgétaires ont des contrôles comptables et ne deviennent pas des tarifs",()=>{
  const b=financial.quebec_budget_2026_2027;
  assert.equal(b.revenus_consolides-b.depenses_consolidees-b.provision_eventualites,b.solde_comptable_avec_provision);
  assert.equal(b.solde_comptable_avec_provision-b.versements_fonds_generations,b.solde_budgetaire);
  const q=financial.ramq_2024_2025;
  assert.equal(q.remuneration_medecins_services_medicaux+q.medicaments_services_pharmaceutiques+q.autres_programmes,q.total_couts_programmes);
  assert.equal(financial.no_default_tariffs_or_savings,true);
  assert.notEqual(q.fiscal_year,b.fiscal_year);
});
test("le registre identifie ses champs financiers et les différences de périmètre",()=>{
  assert.ok(data.champs_financiers_requis.includes("fraisUsagers"));
  assert.ok(data.champs_financiers_requis.includes("transitionAnnuelle"));
  assert.ok(data.regles.some(x=>x.includes("consolidées")));
});
