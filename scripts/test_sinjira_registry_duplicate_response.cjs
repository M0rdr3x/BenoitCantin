'use strict';
// Le vrai module Registre est exécuté en VM avec navigateur/Edge simulés.
// Tests de la frontière HTTP 409 explicite vs panne réseau indéterminée.
// AUCUN compte, fichier privé, API Supabase ou POST réel.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const file=fs.readFileSync(path.join(__dirname,'..','assets/js/sinjira-character-registry.js'),'utf8');
const imports=/^import\s+\{[^;\n]+\}\s+from\s+['"][^'"\n]+['"];?\s*$/gm;
assert.equal([...file.matchAll(imports)].length,1,'Une seule frontière de module Registre attendue');
const script=file.replace(imports,'')+String.raw