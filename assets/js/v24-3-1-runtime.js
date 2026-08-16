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
  if (eyebrow) eyebrow.textContent = 'Registre des Consciences';
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
      if (opt.textContent === 'Personnage moralement ambigu') opt.textContent = 'Personnage nuancé — ni héros ni méchant';
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

// Les anciennes surcharges d'inscription et de Fracture ont été retirées en V24.4.11.
// L'inscription est gérée uniquement par v24-signup.js et Fracture uniquement par
// sinjira-fracture-lobby.js / sinjira-fracture-engine.js. Cela évite les doubles
// gestionnaires submit et les contrôles qui se contredisent.
ready(patchRegistryQuestionnaire);
