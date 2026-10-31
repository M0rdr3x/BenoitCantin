import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';
import { isPermanentNovaSurveyAccount } from '../supabase/functions/_shared/nova_survey_account.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

test('compte permanent vérifié par Auth : admissible à la future porte serveur', () => {
  assert.equal(isPermanentNovaSurveyAccount({id:'compte-fictif',is_anonymous:false}),true);
});
test('comptes anonymes Auth, identité absente et état inconnu : tous refusés fermés', () => {
  for (const user of [
    null,undefined,false,{}, {id:'compte-fictif'}, {id:'',is_anonymous:false},
    {id:'compte-fictif',is_anonymous:true}, {id:'compte-fictif',is_anonymous:null},
    {id:'compte-fictif',is_anonymous:'false'}, {id:45,is_anonymous:false},
    {id:'compte-fictif',is_anonymous:0}
  ]) assert.equal(isPermanentNovaSurveyAccount(user),false);
});
test('les deux Edge Functions doivent vérifier le vrai user Supabase avant RPC', () => {
  for (const name of ['nova-survey-submit','nova-consultation40-submit']) {
    const source=readFileSync(resolve(root,'supabase/functions',name,'index.ts'),'utf8');
    assert.match(source,/import \{ isPermanentNovaSurveyAccount \} from '\.\.\/_shared\/nova_survey_account\.mjs';/);
    assert.match(source,/const user = await requiredUser\(req\);[\s\S]*?if \(!isPermanentNovaSurveyAccount\(user\)\) \{\s*return response\(403, \{ ok: false, code: 'PERMANENT_ACCOUNT_REQUIRED' \} \);\s*\}/);
    const guard=source.indexOf('if (!isPermanentNovaSurveyAccount(user))');
    const rpc=source.indexOf('service.rpc(');
    assert.ok(guard>=0 && rpc>guard,name+' : refus avant agrégation obligatoire');
    assert.match(source,/NOVA(?:40)?_.*COLLECTION_ENABLED/);
  }
});
