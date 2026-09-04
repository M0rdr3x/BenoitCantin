import { getSupabase } from './sinjira-supabase.js';

const PROFILE_FIELDS = ['professional_title','summary','search_status','preferred_location','remote_preference'];
const APPLICATION_STATUSES = new Map([
  ['saved','À considérer'],
  ['applied','Candidature envoyée'],
  ['interview','Entrevue'],
  ['offer','Offre reçue'],
  ['rejected','Non retenue'],
  ['withdrawn','Retirée'],
  ['accepted','Acceptée'],
]);

const statusBox = document.querySelector('[data-employment-status]');
const profileForm = document.querySelector('[data-employment-profile-form]');
const applicationForm = document.querySelector('[data-employment-application-form]');
const applicationList = document.querySelector('[data-employment-applications]');
const refreshButton = document.querySelector('[data-employment-refresh]');

function showStatus(message, kind = 'info') {
  if (!statusBox) return;
  statusBox.hidden = false;
  statusBox.dataset.state = kind;
  statusBox.textContent = message;
}

function clearStatus() {
  if (!statusBox) return;
  statusBox.hidden = true;
  statusBox.textContent = '';
  delete statusBox.dataset.state;
}

function cleanNullable(value, maxLength) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  return text.slice(0, maxLength);
}

function parseSkills(value) {
  const unique = [];
  const seen = new Set();
  for (const raw of String(value ?? '').split(',')) {
    const skill = raw.trim().slice(0, 80);
    const key = skill.toLocaleLowerCase('fr-CA');
    if (!skill || seen.has(key)) continue;
    seen.add(key);
    unique.push(skill);
    if (unique.length === 30) break;
  }
  return unique;
}

function safeHttpUrl(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
    return url.toString().slice(0, 2048);
  } catch (_) {
    return null;
  }
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('fr-CA', { dateStyle: 'medium' }).format(date);
}

function fieldValue(form, name) {
  return form?.elements?.namedItem(name)?.value ?? '';
}

function setFieldValue(form, name, value) {
  const field = form?.elements?.namedItem(name);
  if (field) field.value = value ?? '';
}

function renderEmptyApplications() {
  if (!applicationList) return;
  applicationList.replaceChildren();
  const p = document.createElement('p');
  p.textContent = 'Aucune candidature suivie pour le moment.';
  applicationList.append(p);
}

function renderApplications(rows, supabase, userId) {
  if (!applicationList) return;
  applicationList.replaceChildren();
  if (!rows?.length) {
    renderEmptyApplications();
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'account-reader-grid';

  for (const row of rows) {
    const card = document.createElement('article');
    card.className = 'account-card';

    const eyebrow = document.createElement('span');
    eyebrow.className = 'eyebrow';
    eyebrow.textContent = APPLICATION_STATUSES.get(row.status) ?? 'Candidature';

    const title = document.createElement('h3');
    title.textContent = row.role_title || 'Poste';

    const employer = document.createElement('p');
    const strong = document.createElement('strong');
    strong.textContent = row.employer_name || 'Organisation';
    employer.append(strong);
    if (row.location_label) employer.append(document.createTextNode(` · ${row.location_label}`));

    const dates = document.createElement('p');
    dates.textContent = `Candidature : ${formatDate(row.applied_on)} · Prochaine étape : ${formatDate(row.next_step_on)}`;

    card.append(eyebrow, title, employer, dates);

    if (row.private_notes) {
      const notes = document.createElement('p');
      notes.textContent = row.private_notes;
      card.append(notes);
    }

    if (row.source_url) {
      const href = safeHttpUrl(row.source_url);
      if (href) {
        const source = document.createElement('p');
        const link = document.createElement('a');
        link.href = href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Ouvrir la source originale';
        source.append(link);
        card.append(source);
      }
    }

    const actions = document.createElement('div');
    actions.className = 'hero-actions';

    const statusSelect = document.createElement('select');
    statusSelect.setAttribute('aria-label', `Étape de ${row.role_title || 'la candidature'}`);
    for (const [value, label] of APPLICATION_STATUSES) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      option.selected = row.status === value;
      statusSelect.append(option);
    }
    statusSelect.addEventListener('change', async () => {
      clearStatus();
      const { error } = await supabase
        .from('employment_applications')
        .update({ status: statusSelect.value, updated_at: new Date().toISOString() })
        .eq('id', row.id)
        .eq('user_id', userId);
      if (error) {
        statusSelect.value = row.status;
        showStatus('Impossible de modifier cette candidature pour le moment.', 'error');
        return;
      }
      row.status = statusSelect.value;
      eyebrow.textContent = APPLICATION_STATUSES.get(row.status) ?? 'Candidature';
      showStatus('Étape de candidature mise à jour.', 'success');
    });

    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.className = 'btn btn-secondary';
    deleteButton.textContent = 'Retirer de mon suivi';
    deleteButton.addEventListener('click', async () => {
      if (!window.confirm('Retirer cette candidature de votre suivi privé ?')) return;
      const { error } = await supabase
        .from('employment_applications')
        .delete()
        .eq('id', row.id)
        .eq('user_id', userId);
      if (error) {
        showStatus('Impossible de retirer cette candidature pour le moment.', 'error');
        return;
      }
      card.remove();
      if (!grid.children.length) renderEmptyApplications();
      showStatus('Candidature retirée de votre suivi.', 'success');
    });

    actions.append(statusSelect, deleteButton);
    card.append(actions);
    grid.append(card);
  }

  applicationList.append(grid);
}

async function loadProfile(supabase, userId) {
  if (!profileForm) return;
  const { data, error } = await supabase
    .from('employment_profiles')
    .select('professional_title,summary,search_status,preferred_location,remote_preference,skills')
    .eq('user_id', userId)
    .maybeSingle();

  if (error) throw error;
  if (!data) return;
  for (const field of PROFILE_FIELDS) setFieldValue(profileForm, field, data[field]);
  setFieldValue(profileForm, 'skills', Array.isArray(data.skills) ? data.skills.join(', ') : '');
}

async function loadApplications(supabase, userId) {
  if (!applicationList) return;
  const { data, error } = await supabase
    .from('employment_applications')
    .select('id,employer_name,role_title,location_label,source_url,status,applied_on,next_step_on,private_notes,created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
  if (error) throw error;
  renderApplications(data ?? [], supabase, userId);
}

async function init() {
  const supabase = getSupabase();
  const { data: { user }, error: userError } = await supabase.auth.getUser();
  if (userError || !user) {
    showStatus('Connectez-vous à votre compte SINJIRA pour utiliser Emploi.', 'error');
    return;
  }

  try {
    await Promise.all([loadProfile(supabase, user.id), loadApplications(supabase, user.id)]);
  } catch (_) {
    showStatus('Le module Emploi n’est pas disponible pour le moment. Vos autres espaces SINJIRA restent inchangés.', 'error');
  }

  profileForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearStatus();
    const payload = {
      user_id: user.id,
      professional_title: cleanNullable(fieldValue(profileForm, 'professional_title'), 120),
      summary: cleanNullable(fieldValue(profileForm, 'summary'), 3000),
      search_status: fieldValue(profileForm, 'search_status') || 'not_looking',
      preferred_location: cleanNullable(fieldValue(profileForm, 'preferred_location'), 160),
      remote_preference: fieldValue(profileForm, 'remote_preference') || 'flexible',
      skills: parseSkills(fieldValue(profileForm, 'skills')),
      updated_at: new Date().toISOString(),
    };
    const { error } = await supabase.from('employment_profiles').upsert(payload, { onConflict: 'user_id' });
    if (error) {
      showStatus('Impossible d’enregistrer votre profil Emploi pour le moment.', 'error');
      return;
    }
    showStatus('Votre profil Emploi privé est enregistré.', 'success');
  });

  applicationForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearStatus();
    const sourceInput = fieldValue(applicationForm, 'source_url').trim();
    const sourceUrl = safeHttpUrl(sourceInput);
    if (sourceInput && !sourceUrl) {
      showStatus('Le lien source doit commencer par http:// ou https://.', 'error');
      return;
    }
    const employerName = cleanNullable(fieldValue(applicationForm, 'employer_name'), 160);
    const roleTitle = cleanNullable(fieldValue(applicationForm, 'role_title'), 160);
    if (!employerName || !roleTitle) {
      showStatus('Indiquez l’organisation et le poste.', 'error');
      return;
    }
    const payload = {
      user_id: user.id,
      employer_name: employerName,
      role_title: roleTitle,
      location_label: cleanNullable(fieldValue(applicationForm, 'location_label'), 160),
      source_url: sourceUrl,
      status: fieldValue(applicationForm, 'status') || 'saved',
      applied_on: cleanNullable(fieldValue(applicationForm, 'applied_on'), 10),
      next_step_on: cleanNullable(fieldValue(applicationForm, 'next_step_on'), 10),
      private_notes: cleanNullable(fieldValue(applicationForm, 'private_notes'), 5000),
    };
    const { error } = await supabase.from('employment_applications').insert(payload);
    if (error) {
      showStatus('Impossible d’ajouter cette candidature pour le moment.', 'error');
      return;
    }
    applicationForm.reset();
    showStatus('Candidature ajoutée à votre suivi privé.', 'success');
    try { await loadApplications(supabase, user.id); } catch (_) {}
  });

  refreshButton?.addEventListener('click', async () => {
    clearStatus();
    try {
      await loadApplications(supabase, user.id);
      showStatus('Votre suivi est à jour.', 'success');
    } catch (_) {
      showStatus('Impossible d’actualiser votre suivi pour le moment.', 'error');
    }
  });
}

init().catch(() => showStatus('Le module Emploi n’est pas disponible pour le moment.', 'error'));
