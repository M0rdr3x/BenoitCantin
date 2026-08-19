import {getSupabase} from './sinjira-social-common.js?v=24.4.42';

const EDITABLE_TABLES=new Set([
  'social_real_posts',
  'social_real_comments',
  'social_character_posts',
  'social_character_comments'
]);

function allowedTable(table){
  if(!EDITABLE_TABLES.has(table))throw new Error('SOCIAL_CONTENT_TABLE_NOT_ALLOWED');
  return table;
}

export function editedSuffix(row={}){
  const created=Date.parse(row.created_at||'');
  const updated=Date.parse(row.updated_at||'');
  return Number.isFinite(created)&&Number.isFinite(updated)&&updated-created>1000?' · modifié':'';
}

export async function editOwnContent({table,id,current,max,label='ce contenu'}){
  allowedTable(table);
  const next=prompt(`Modifier ${label} :`,String(current||''));
  if(next===null)return false;
  const body=next.trim();
  if(!body){alert('Le texte ne peut pas être vide.');return false;}
  if(body.length>max){alert(`Le texte doit contenir au maximum ${max} caractères.`);return false;}
  const {error}=await getSupabase().from(table).update({body}).eq('id',id);
  if(error)throw error;
  return true;
}

export async function deleteOwnContent({table,id,label='ce contenu'}){
  allowedTable(table);
  if(!confirm(`Supprimer ${label}? Cette action est définitive.`))return false;
  const {error}=await getSupabase().from(table).delete().eq('id',id);
  if(error)throw error;
  return true;
}
