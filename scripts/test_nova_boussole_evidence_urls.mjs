import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const js = readFileSync("projets/projet-nova/assets/boussole-electorale.js", "utf8");
const evidence = JSON.parse(readFileSync("projets/projet-nova/data/boussole-preuves-2026.json", "utf8"));
const match = js.match(/  function verifiedDocumentUrl\(raw\)\{[\s\S]*?\n  \}/);
assert.ok(match, "Validateur HTTPS documentaire absent");

const check = runInNewContext(match[0] + "\nverifiedDocumentUrl", { URL });
for (const unsafe of [
  "", null, 4, "javascript:alert(1)", "data:text/html,hello",
  "http://example.org/doc", "//example.org/doc",
  "https://user@example.org/doc", "https://user:password@example.org/doc",
  "file:///etc/passwd", "mailto:someone@example.org",
]) {
  assert.equal(check(unsafe), null, "URL non sécurisée acceptée: " + unsafe);
}
assert.equal(check("https://example.org/document?q=1"), "https://example.org/document?q=1");
assert.match(js, /href="\$\{esc\(sourceUrl\)\}"/, "Lien documentaire non échappé");
assert.match(js, /if\(!verifiedDocumentUrl\(record\.sourceUrl\)\)/, "Refus des preuves non HTTPS manquant");

const finalized = evidence.evidenceRecords.filter(
  record => record.finalizable === true && record.secondIndependentReview?.status === "completed"
);
assert.ok(finalized.length > 0, "Aucune preuve finalisée");
for (const record of finalized) {
  assert.ok(check(record.sourceUrl), "Preuve finale sans URL sûre: " + record.recordId);
}
console.log("OK Boussole: URL externes verrouillées, tests malveillants, " + finalized.length + " preuves finalisées conformes.");
