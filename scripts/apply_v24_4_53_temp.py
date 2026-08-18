from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# Trigger d’application contrôlée V24.4.53 — aucun changement fonctionnel dans ce fichier temporaire.
# 1) Admin HTML: user-facing identifier replaces visible slug field.
p=ROOT/'admin/sinjira/index.html'
text=p.read_text('utf-8')
old='<div class="field"><label>Nom</label><input name="name" required=""/></div><div class="field"><label>Slug</label><input name="slug" required=""/></div>'
new='<div class="field"><label>Identifiant de projet</label><input name="name" required="" placeholder="Ex. Fracture du Réseau-Mère"/><small style="display:block;margin-top:6px;color:var(--muted)">Nom lisible utilisé dans l’administration et les sélecteurs. L’identifiant technique des URL est généré automatiquement et reste stable.</small></div><input name="slug" type="hidden"/>'
if old not in text: raise SystemExit('bloc Nom/Slug introuvable')
text=text.replace(old,new)
text=text.replace('sinjira-admin-console.js?v=2.0','sinjira-admin-console.js?v=24.4.53')
p.write_text(text,'utf-8')

# 2) Frontend admin: never show technical slug as the user-facing identifier.
p=ROOT/'assets/js/sinjira-admin-console.js'
text=p.read_text('utf-8')
old="<strong>${escapeHtml(p.name)} · ${escapeHtml(p.slug)}</strong><span>${escapeHtml(p.type)} · ${escapeHtml(p.status)} · ${escapeHtml(p.visibility)}</span>"
new="<strong>${escapeHtml(p.name)}</strong><span>Identifiant de projet · ${escapeHtml(p.type)} · ${escapeHtml(p.status)} · ${escapeHtml(p.visibility)}</span>"
if old not in text: raise SystemExit('renderProjects slug visible introuvable')
text=text.replace(old,new)
p.write_text(text,'utf-8')

# 3) Server admin-console: generated slug for new project, immutable slug for existing project.
p=ROOT/'supabase/functions/admin-console/index.ts'
text=p.read_text('utf-8')
needle="""function safeName(v:string){
  return String(v||'document').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()
    .replace(/[^a-z0-9._-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,120)||'document';
}
"""
insert=needle+"""function safeProjectSlug(v:string){
  return String(v||'projet').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()
    .replace(/[^a-z0-9]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,96)||'projet';
}
"""
if needle not in text: raise SystemExit('safeName introuvable')
text=text.replace(needle,insert)
old="""    if(action==='save_project'){
      const p=body.project||{},payload:any={
        slug:String(p.slug||'').trim(),name:String(p.name||'').trim(),type:p.type||'game',
        status:p.status||'development',visibility:p.visibility||'account',
        description:String(p.description||'').slice(0,5000),cover_url:p.cover_url||null,
        public_path:p.public_path||null,play_path:p.play_path||null,
        allow_tester_requests:p.allow_tester_requests!==false,sort_order:Number(p.sort_order||100)
      };
      if(p.id)payload.id=p.id;
      if(!payload.slug||!payload.name)return json({ok:false,error:'Nom et slug requis.'},400);
      const {data,error}=await service.from('projects').upsert(payload).select('*').single();
      if(error)throw error;return json({ok:true,project:data});
    }
"""
new="""    if(action==='save_project'){
      const p=body.project||{},name=String(p.name||'').trim();
      if(!name)return json({ok:false,error:'Identifiant de projet requis.'},400);
      let slug='';
      if(p.id){
        const {data:existing,error:existingError}=await service.from('projects').select('slug').eq('id',p.id).single();
        if(existingError)throw existingError;
        slug=String(existing?.slug||'').trim();
      }
      if(!slug)slug=safeProjectSlug(name);
      const payload:any={
        slug,name,type:p.type||'game',status:p.status||'development',visibility:p.visibility||'account',
        description:String(p.description||'').slice(0,5000),cover_url:p.cover_url||null,
        public_path:p.public_path||null,play_path:p.play_path||null,
        allow_tester_requests:p.allow_tester_requests!==false,sort_order:Number(p.sort_order||100)
      };
      if(p.id)payload.id=p.id;
      const {data,error}=await service.from('projects').upsert(payload).select('*').single();
      if(error){
        if(String(error.code||'')==='23505')return json({ok:false,error:'Cet identifiant de projet produit déjà la même URL technique. Choisissez un identifiant plus distinct.'},409);
        throw error;
      }
      return json({ok:true,project:data});
    }
"""
if old not in text: raise SystemExit('save_project historique introuvable')
text=text.replace(old,new)
p.write_text(text,'utf-8')

# 4) Permanent contract validator.
p=ROOT/'scripts/validate_project_identifier_ui.py'
p.write_text('''#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'admin/sinjira/index.html').read_text('utf-8')
JS=(ROOT/'assets/js/sinjira-admin-console.js').read_text('utf-8')
SERVER=(ROOT/'supabase/functions/admin-console/index.ts').read_text('utf-8')
errors=[]
def need(cond,msg):
    if not cond: errors.append(msg)
need('Identifiant de projet' in HTML,'libellé Identifiant de projet absent')
need('<label>Slug</label>' not in HTML,'Slug technique encore visible comme champ utilisateur')
need('name="slug" type="hidden"' in HTML,'slug technique non conservé en champ caché')
need('Fracture du Réseau-Mère' in HTML,'exemple utilisateur Fracture du Réseau-Mère absent')
need('Identifiant de projet ·' in JS,'liste des projets ne présente pas le nouvel identifiant')
need('${escapeHtml(p.slug)}' not in JS,'slug technique encore affiché dans la liste')
need('function safeProjectSlug' in SERVER,'génération serveur du slug absente')
need("if(p.id){" in SERVER and ".select('slug').eq('id',p.id).single()" in SERVER,'slug existant non verrouillé lors des modifications')
need("if(!slug)slug=safeProjectSlug(name)" in SERVER,'slug nouveau projet non généré automatiquement')
need("Identifiant de projet requis." in SERVER,'validation serveur encore formulée en slug')
if errors:
    print(f'ECHEC identifiant projet V24.4.53: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK identifiant projet V24.4.53: nom lisible côté admin, slug technique automatique et stable côté serveur.')
''','utf-8')

# 5) CI hook.
p=ROOT/'.github/workflows/validate-site.yml'
text=p.read_text('utf-8')
needle='      - name: Vérifier la parité client/serveur de l’administration V24.4.50\n        run: python scripts/validate_admin_action_contract.py\n'
add=needle+'      - name: Vérifier l’identifiant de projet V24.4.53\n        run: python scripts/validate_project_identifier_ui.py\n'
if needle not in text: raise SystemExit('CI admin contract hook introuvable')
text=text.replace(needle,add)
p.write_text(text,'utf-8')
print('V24.4.53 applied')
