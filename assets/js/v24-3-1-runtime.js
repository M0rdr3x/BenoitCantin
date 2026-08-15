import {
  getSupabase,
  getCurrentUser,
  isSinjiraOwner,
  setStatus,
  SINJIRA_CONFIG,
  isSinjiraBackendConfigured
} from './sinjira-supabase.js';

const path = window.location.pathname;

function ready(fn) {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, { once: true });
  else fn();
}

function fieldLabel(name, text) {
  const node = document.querySelector(`[name="${name}"]`);
  const label = node?.closest('.field')?.querySelector('label');
  if (label) label.textContent = text;
}

function patchScale(name, left, right) {
  const select = document.querySelector(`select[name="${name}"]`);
  const span = select?.closest('.v24-scale')?.querySelector('span');
  const strong = span?.querySelector('strong');
  const bold = span?.querySelector('b');
  if (strong) strong.textContent = left;
  if (bold) bold.textContent = right;
}

function patchRegistryQuestionnaire() {
  if (!path.startsWith('/projets/sinjira/registre')) return;

  const eyebrow = document.querySelector('.v24-hero .eyebrow');
  if (eyebrow) eyebrow.textContent = 'Questionnaire V24.3.1';
  const title = document.querySelector('.v24-hero h1');
  if (title) title.innerHTML = 'Complet, mais simple<br>à comprendre.';
  const intro = document.querySelector('.v24-hero h1 + p');
  if (intro) intro.textContent = 'La version détaillée du questionnaire est conservée. Seules les formulations ambiguës, trop techniques ou inutilement difficiles ont été simplifiées.';

  const scaleLegend = document.querySelector('.v24-scale-legend');
  if (scaleLegend) scaleLegend.innerHTML = '<strong>Échelle 1 à 5 :</strong> 1 = vous ressemble surtout au choix de gauche · 3 = entre les deux · 5 = vous ressemble surtout au choix de droite.';

  patchScale('scale_reserved_social', 'Plutôt réservé', 'Plutôt sociable');
  patchScale('scale_cautious_bold', 'Prudent', 'Prend facilement des risques');
  patchScale('scale_calm_impulsive', 'Réfléchit avant d’agir', 'Agit rapidement');
  patchScale('scale_logic_instinct', 'S’appuie sur la logique', 'S’appuie sur son instinct');
  patchScale('scale_conciliatory_confrontational', 'Cherche le compromis', 'Affronte directement');
  patchScale('scale_follower_leader', 'Préfère suivre', 'Aime prendre les devants');
  patchScale('scale_wary_trusting', 'Fait difficilement confiance', 'Fait facilement confiance');
  patchScale('scale_flexible_rigid', 'Préfère improviser', 'Préfère planifier');

  fieldLabel('narrative_role', 'Type de rôle qui vous plairait');
  fieldLabel('narrative_importance', 'Taille du rôle souhaité');
  fieldLabel('moral_orientation', 'Façon générale d’agir');
  fieldLabel('placement_preference', 'Où votre personnage pourrait exister');
  fieldLabel('prohibited_elements', 'Y a-t-il quelque chose que vous ne voulez pas voir utilisé pour votre personnage ?');

  const role = document.querySelector('select[name="narrative_role"]');
  if (role) {
    [...role.options].forEach((opt) => {
      if (opt.textContent === 'Personnage moralement ambigu') {
        opt.textContent = 'Personnage nuancé — ni héros ni méchant';
      }
    });
  }

  const moral = document.querySelector('select[name="moral_orientation"]');
  if (moral) {
    [...moral.options].forEach((opt) => {
      if (opt.textContent === 'Moralement ambigu') opt.textContent = 'Variable selon la situation';
      if (opt.textContent === 'Peut évoluer avec l’histoire') opt.textContent = 'Peut changer avec ce qu’il vit';
      if (opt.textContent === 'L’auteur peut décider librement') opt.textContent = 'L’auteur peut décider';
    });
  }

  const prohibited = document.querySelector('textarea[name="prohibited_elements"]');
  if (prohibited) prohibited.placeholder = 'Facultatif. Ex. un sujet personnel, une situation ou un élément que vous préférez exclure.';

  const fieldsets = [...document.querySelectorAll('fieldset.v24-fieldset')];
  const last = fieldsets.find((fs) => fs.querySelector('textarea[name="additional_notes"], textarea[name="free_text"], textarea[name="personality_notes"]')) || fieldsets[fieldsets.length - 1];
  const lastLegend = last?.querySelector('legend');
  if (lastLegend && /seule question libre|question libre/i.test(lastLegend.textContent || '')) lastLegend.textContent = '8. Un dernier détail, si vous voulez';

  const submitButton = document.querySelector('[data-character-form] button[type="submit"]');
  if (submitButton) submitButton.textContent = 'Enregistrer mon questionnaire';
}

function patchSignupQuestionnaire() {
  if (path !== '/compte/inscription.html' && path !== '/compte/inscription') return;
  const form = document.querySelector('[data-signup-form]');
  const toggle = document.querySelector('[data-v24-questionnaire-toggle]');
  const details = document.querySelector('[data-v24-questionnaire]');
  if (!form || !toggle || !details) return;

  toggle.name = 'wants_character_questionnaire';
  toggle.value = 'yes';
  const toggleText = toggle.closest('label')?.querySelector('span');
  if (toggleText) toggleText.textContent = 'Après la création du compte, je veux remplir le questionnaire complet du Registre.';

  const fieldset = details.closest('fieldset');
  const legend = fieldset?.querySelector('legend');
  if (legend) legend.textContent = 'Personnage SINJIRA™ — facultatif';
  details.hidden = false;
  details.innerHTML = '<p class="v24-callout"><strong>Un seul questionnaire officiel.</strong> Nous avons retiré le petit questionnaire rapide pour éviter les doublons et les réponses contradictoires. Le Registre complet reste facultatif et peut être rempli après la création du compte.</p><p><a class="btn btn-secondary" href="/projets/sinjira/registre/">Voir le questionnaire complet</a></p>';

  const status = document.querySelector('[data-account-status]');

  document.addEventListener('submit', async (event) => {
    if (event.target !== form) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    if (!isSinjiraBackendConfigured()) {
      setStatus(status, 'Supabase doit d’abord être configuré.', 'error');
      return;
    }

    const d = new FormData(form);
    const password = String(d.get('password') || '');
    const confirmation = String(d.get('password_confirm') || '');
    if (password.length < 12) {
      setStatus(status, 'Utilisez un mot de passe d’au moins 12 caractères.', 'error');
      return;
    }
    if (password !== confirmation) {
      setStatus(status, 'Les mots de passe ne correspondent pas.', 'error');
      return;
    }

    const contributor = d.get('initial_contributor_opt_in') === 'yes';
    const wantsQuestionnaire = d.get('wants_character_questionnaire') === 'yes';
    const languages = String(d.get('languages') || '').split(',').map((x) => x.trim()).filter(Boolean).slice(0, 12);
    const metadata = {
      pseudo: String(d.get('pseudo') || '').trim(),
      display_name: String(d.get('display_name') || '').trim(),
      birth_date: String(d.get('birth_date') || ''),
      gender: String(d.get('gender') || ''),
      languages,
      residence_city: String(d.get('residence_city') || '').trim(),
      residence_region: String(d.get('residence_region') || '').trim(),
      residence_country: String(d.get('residence_country') || '').trim(),
      origin_city: String(d.get('origin_city') || '').trim(),
      origin_region: String(d.get('origin_region') || '').trim(),
      origin_country: String(d.get('origin_country') || '').trim(),
      relationship_status: String(d.get('relationship_status') || ''),
      relationship_since: String(d.get('relationship_since') || ''),
      relationship_partner_label: String(d.get('relationship_partner_label') || '').trim(),
      fill_character_now: false,
      wants_character_questionnaire: wantsQuestionnaire,
      initial_contributor_opt_in: contributor,
      initial_share_free_text: contributor && d.get('share_free_text') === 'yes'
    };

    const { data, error } = await getSupabase().auth.signUp({
      email: String(d.get('email') || '').trim(),
      password,
      options: {
        emailRedirectTo: `${SINJIRA_CONFIG.siteUrl}/compte/index.html`,
        data: metadata
      }
    });

    if (error) {
      setStatus(status, error.message, 'error');
      return;
    }

    if (data.session) {
      window.location.href = wantsQuestionnaire ? '/projets/sinjira/registre/' : '/compte/index.html';
      return;
    }

    setStatus(
      status,
      wantsQuestionnaire
        ? 'Compte créé. Vérifiez votre courriel, puis connectez-vous et ouvrez le Registre pour remplir le questionnaire complet.'
        : 'Compte créé. Vérifiez votre courriel pour confirmer votre adresse.',
      'success'
    );
    form.reset();
  }, true);
}

let fractureAccess = null;

function fractureAccessMessage(state, detail = '') {
  const host = document.querySelector('[data-fracture-access-status]') || (() => {
    const node = document.createElement('div');
    node.dataset.fractureAccessStatus = '';
    node.className = 'v24-callout';
    const firstForm = document.querySelector('[data-create-party], [data-join-party]');
    if (firstForm) firstForm.parentElement?.insertBefore(node, firstForm);
    else document.querySelector('main')?.prepend(node);
    return node;
  })();

  if (state === 'allowed') {
    host.innerHTML = '<strong>Accès Fracture vérifié.</strong> Vous pouvez créer ou rejoindre une partie.';
  } else if (state === 'owner') {
    host.innerHTML = '<strong>Accès propriétaire AbyssTime.</strong> Fracture du Réseau-Mère est entièrement déverrouillé pour ce compte.';
  } else if (state === 'denied') {
    host.innerHTML = '<strong>Accès Fracture requis.</strong> Chaque joueur doit posséder une licence physique activée ou une licence numérique. <a href="/compte/licences.html">Gérer mes licences</a>.';
  } else if (state === 'error') {
    host.innerHTML = `<strong>Vérification de licence indisponible.</strong> ${detail || 'La mise à jour serveur V24.3.1 doit être appliquée avant de jouer.'}`;
  } else {
    host.textContent = 'Vérification de votre accès Fracture…';
  }
}

function setFractureFormsEnabled(enabled) {
  document.querySelectorAll('[data-create-party], [data-join-party]').forEach((form) => {
    form.querySelectorAll('input,select,button').forEach((control) => {
      control.disabled = !enabled;
    });
  });
}

async function patchFractureLobby() {
  const isFracture = path.startsWith('/projets/sinjira/jeux/fracture-du-reseau-mere');
  if (!isFracture) return;

  const isLobby = /\/jouer\.html$/.test(path) || /\/jouer\/?$/.test(path);
  const main = document.querySelector('main');
  if (main && !document.querySelector('[data-v2431-fracture-mode]')) {
    const note = document.createElement('section');
    note.dataset.v2431FractureMode = '';
    note.className = 'section section-tight';
    note.innerHTML = '<div class="container"><div class="v24-callout"><strong>Mode Web V24.3.1 :</strong> le site gère le salon de partie, les joueurs, les fiches privées synchronisées et la fin de partie. Le moteur 100 % numérique qui distribuera les cartes, protégera les mains cachées et validera automatiquement chaque action sera ajouté dans une étape suivante.</div></div>';
    const firstSection = main.querySelector('section');
    if (firstSection?.nextSibling) main.insertBefore(note, firstSection.nextSibling);
    else main.appendChild(note);
  }

  if (!isLobby) return;

  setFractureFormsEnabled(false);
  fractureAccessMessage('checking');

  const user = await getCurrentUser();
  if (!user) {
    fractureAccess = false;
    fractureAccessMessage('error', 'Connectez-vous à votre Compte SINJIRA™ pour vérifier votre licence.');
    return;
  }
  if (isSinjiraOwner(user)) {
    fractureAccess = true;
    setFractureFormsEnabled(true);
    fractureAccessMessage('owner');
    return;
  }

  try {
    const { data, error } = await getSupabase().rpc('has_sinjira_product', {
      p_product_slug: 'fracture-du-reseau-mere',
      p_user_id: user.id
    });
    if (error) throw error;
    fractureAccess = data === true;
    setFractureFormsEnabled(fractureAccess);
    fractureAccessMessage(fractureAccess ? 'allowed' : 'denied');
  } catch (error) {
    fractureAccess = false;
    fractureAccessMessage('error', 'Le serveur de licences n’est pas encore à jour.');
  }

  document.addEventListener('submit', (event) => {
    if (!event.target?.matches?.('[data-create-party], [data-join-party]')) return;
    if (fractureAccess === true) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    fractureAccessMessage(fractureAccess === false ? 'denied' : 'checking');
  }, true);
}

ready(() => {
  patchRegistryQuestionnaire();
  patchSignupQuestionnaire();
  patchFractureLobby();
});
