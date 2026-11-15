import {ALL_FIELDS, comparerScenarios} from "./comparateur-financier-core.mjs";

const form = document.getElementById("finance-service-form");
const resultats = document.getElementById("finance-results");
const erreur = document.getElementById("finance-error");
const selectMode = document.getElementById("mode-alternatif");
const monnaie = new Intl.NumberFormat("fr-CA",{style:"currency",currency:"CAD",maximumFractionDigits:2});
const nombre = new Intl.NumberFormat("fr-CA",{maximumFractionDigits:2});
const afficherMontant = (x) => monnaie.format(x);

function scenario(prefixe) {
  const s = {};
  for(const champ of ALL_FIELDS) {
    const el = form.elements.namedItem(prefixe + "_" + champ);
    if(!el || el.value.trim()==="") throw new Error("Tous les montants sont requis, y compris 0 $ pour une rubrique non applicable.");
    const valeur = Number(el.value);
    if(!Number.isFinite(valeur) || valeur<0) throw new Error("Un montant est invalide dans le scénario " + prefixe + ".");
    s[champ]=valeur;
  }
  return s;
}
function remplir(id, valeur) {
  const el=document.getElementById(id);
  if(el) el.textContent=afficherMontant(valeur);
}
form?.addEventListener("submit",event=>{
  event.preventDefault();
  resultatMasque();
  if(!form.checkValidity()){form.reportValidity();return;}
  try {
    const volume = Number(form.elements.namedItem("volumeAnnuel").value);
    const r = comparerScenarios(volume,scenario("reference"),scenario("alternative"));
    document.getElementById("result-volume").textContent=nombre.format(volume);
    document.getElementById("result-mode").textContent=selectMode.options[selectMode.selectedIndex].textContent;
    remplir("result-public-reference",r.reference.coutPublicAnnuel);
    remplir("result-public-alternative",r.alternative.coutPublicAnnuel);
    remplir("result-public-delta",r.deltaPublicAnnuel);
    remplir("result-social-reference",r.reference.coutSocialAnnuel);
    remplir("result-social-alternative",r.alternative.coutSocialAnnuel);
    remplir("result-social-delta",r.deltaSocialAnnuel);
    remplir("result-public-delta-unitaire",r.deltaPublicUnitaire);
    remplir("result-social-delta-unitaire",r.deltaSocialUnitaire);
    resultats.hidden=false;
    erreur.textContent="";
  } catch(e) {
    erreur.textContent=e instanceof Error?e.message:"Impossible de traiter les valeurs.";
    resultats.hidden=true;
    erreur.focus();
  }
});
function resultatMasque(){resultats.hidden=true;erreur.textContent="";}
form?.addEventListener("reset",resultatMasque);
