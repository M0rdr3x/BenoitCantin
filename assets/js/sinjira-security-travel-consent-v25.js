import { setStatus } from './sinjira-supabase.js';

const FORM_SELECTOR = '[data-security-travel-form]';
const PREVIEW_SELECTOR = '[data-security-travel-preview]';
const SUBMIT_SELECTOR = 'button[type="submit"]';
let approvedSignature = null;
let securityReady = document.documentElement.dataset.securityCenterReady === 'true';

function qs(selector, root = document){
  return root.querySelector(selector);
}

function status(message, type = 'info'){
  setStatus(qs('[data-security-center-status]'), message, type);
}

function setTravelLocked(form, locked){
  for(const el of form?.elements || [])el.disabled = locked;
}

function normalizeDestinations(value){
  const destinations = [];
  const seen = new Set();
  for(const raw of String(value || '').split(',')){
    const code = raw.trim().toUpperCase();
    if(!code)continue;
    if(!/^[A-Z]{2}$/.test(code))throw new Error('Utilisez uniquement des codes pays à 2 lettres, par exemple MA, FR ou CA.');
    if(seen.has(code))continue;
    seen.add(code);
    destinations.push(code);
  }
  if(!destinations.length)throw new Error('Indiquez au moins un pays prévu.');
  if(destinations.length > 12)throw new Error('Le Mode Voyage accepte au maximum 12 pays.');
  return destinations;
}

function readTravelDraft(form){
  const data = new FormData(form);
  const startsAtInput = String(data.get('starts_at') || '').trim();
  const endsAtInput = String(data.get('ends_at') || '').trim();
  const destinations = normalizeDestinations(data.get('destinations'));
  if(!startsAtInput || !endsAtInput)throw new Error('Indiquez une date de départ et une date de retour.');

  const startsAt = new Date(startsAtInput);
  const endsAt = new Date(endsAtInput);
  if(Number.isNaN(startsAt.getTime()) || Number.isNaN(endsAt.getTime()))throw new Error('La période du voyage est invalide.');
  if(endsAt <= startsAt)throw new Error('La date de retour doit être postérieure à la date de départ.');

  const destinationInput = form.elements.namedItem('destinations');
  if(destinationInput instanceof HTMLInputElement)destinationInput.value = destinations.join(', ');

  return {
    startsAt: startsAt.toISOString(),
    endsAt: endsAt.toISOString(),
    destinations,
    multiCountry: data.get('multi_country') === 'on'
  };
}

function travelSignature(draft){
  return JSON.stringify([draft.startsAt, draft.endsAt, draft.destinations, draft.multiCountry]);
}

function formatMoment(iso){
  const locale = document.documentElement.lang || 'fr-CA';
  return new Intl.DateTimeFormat(locale, {dateStyle:'medium', timeStyle:'short'}).format(new Date(iso));
}

function appendPreviewRow(list, label, value, key){
  const term = document.createElement('dt');
  const description = document.createElement('dd');
  term.textContent = label;
  description.textContent = value;
  if(key)description.dataset[key] = '';
  list.append(term, description);
  return description;
}

function ensurePreview(form){
  let preview = qs(PREVIEW_SELECTOR, form);
  if(preview)return preview;

  preview = document.createElement('section');
  preview.className = 'security-item';
  preview.dataset.securityTravelPreview = '';
  preview.hidden = true;
  preview.setAttribute('aria-live', 'polite');
  preview.setAttribute('aria-atomic', 'true');

  const heading = document.createElement('h3');
  heading.textContent = 'Vérifiez avant d’activer';
  const list = document.createElement('dl');
  appendPreviewRow(list, 'Pays prévus', '', 'travelPreviewDestinations');
  appendPreviewRow(list, 'Départ', '', 'travelPreviewStart');
  appendPreviewRow(list, 'Retour', '', 'travelPreviewEnd');
  appendPreviewRow(list, 'Plusieurs pays', '', 'travelPreviewMultiCountry');

  const privacy = document.createElement('p');
  privacy.className = 'v24-feature-note';
  privacy.textContent = 'Aucune donnée de ce voyage n’est envoyée au serveur avant votre confirmation. Seuls ces codes pays, cette période et l’indication multi-pays seront transmis — jamais de GPS, d’adresse, d’hôtel, de vol ou de trajet quotidien.';

  preview.append(heading, list, privacy);
  const submit = qs(SUBMIT_SELECTOR, form);
  if(submit)form.insertBefore(preview, submit);
  else form.append(preview);
  return preview;
}

function resetPreview(form){
  approvedSignature = null;
  delete form.dataset.travelConsentApproved;
  const preview = qs(PREVIEW_SELECTOR, form);
  if(preview)preview.hidden = true;
  const submit = qs(SUBMIT_SELECTOR, form);
  if(submit)submit.textContent = 'Vérifier avant d’activer';
}

function showPreview(form, draft){
  const preview = ensurePreview(form);
  qs('[data-travel-preview-destinations]', preview).textContent = draft.destinations.join(', ');
  qs('[data-travel-preview-start]', preview).textContent = formatMoment(draft.startsAt);
  qs('[data-travel-preview-end]', preview).textContent = formatMoment(draft.endsAt);
  qs('[data-travel-preview-multi-country]', preview).textContent = draft.multiCountry ? 'Oui' : 'Non';
  preview.hidden = false;
  const submit = qs(SUBMIT_SELECTOR, form);
  if(submit)submit.textContent = 'Confirmer et activer le Mode Voyage';
}

function interceptTravelSubmit(event){
  const form = event.target?.closest?.(FORM_SELECTOR);
  if(!form)return;

  if(!securityReady){
    event.preventDefault();
    event.stopImmediatePropagation();
    resetPreview(form);
    status('Le Centre de sécurité termine son chargement. Le Mode Voyage reste verrouillé jusqu’à ce que les protections du compte soient prêtes.', 'info');
    return;
  }

  if(navigator.onLine === false){
    event.preventDefault();
    event.stopImmediatePropagation();
    resetPreview(form);
    status('Vous êtes hors ligne. Le Mode Voyage n’a pas été activé. Reconnectez-vous, puis vérifiez à nouveau les données.', 'error');
    return;
  }

  try{
    const draft = readTravelDraft(form);
    const signature = travelSignature(draft);
    if(approvedSignature === signature){
      form.dataset.travelConsentApproved='true';
      return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();
    approvedSignature = signature;
    delete form.dataset.travelConsentApproved;
    showPreview(form, draft);
    status('Vérifiez les données affichées, puis confirmez vous-même l’activation du Mode Voyage.', 'info');
  }catch(error){
    event.preventDefault();
    event.stopImmediatePropagation();
    resetPreview(form);
    status(error?.message || 'Impossible de préparer le Mode Voyage.', 'error');
  }
}

function initTravelConsent(){
  const form = qs(FORM_SELECTOR);
  if(!form)return;
  ensurePreview(form);
  resetPreview(form);
  securityReady = document.documentElement.dataset.securityCenterReady === 'true';
  setTravelLocked(form, !securityReady);
  form.addEventListener('input', () => resetPreview(form));
  form.addEventListener('change', () => resetPreview(form));
  form.addEventListener('reset', () => queueMicrotask(() => resetPreview(form)));
}

document.addEventListener('submit', interceptTravelSubmit, true);

window.addEventListener('offline', () => {
  const form = qs(FORM_SELECTOR);
  if(!form)return;
  resetPreview(form);
  status('Connexion perdue. Toute confirmation du Mode Voyage doit être refaite après reconnexion.', 'error');
});

window.addEventListener('online', () => {
  const form = qs(FORM_SELECTOR);
  if(!form)return;
  resetPreview(form);
  status('Connexion rétablie. Vérifiez à nouveau votre voyage avant de l’activer.', 'info');
});

window.addEventListener('sinjira:security-center-ready', () => {
  const form = qs(FORM_SELECTOR);
  securityReady = true;
  if(!form)return;
  setTravelLocked(form, false);
  resetPreview(form);
  status('Mode Voyage prêt. Vérifiez vos données avant toute activation.', 'info');
});

if(document.readyState === 'loading')document.addEventListener('DOMContentLoaded', initTravelConsent, {once:true});
else initTravelConsent();
