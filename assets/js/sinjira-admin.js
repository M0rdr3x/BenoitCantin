import {
  getSupabase,
  requireUser,
  setStatus,
  isSinjiraBackendConfigured
} from './sinjira-supabase.js';

const status = document.querySelector('[data-admin-status]');

function renderCard(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = String(value ?? '—');
}

// Les libellés proviennent de contributions persistées. Aucun champ ne doit
// passer par innerHTML, même si la fonction Edge exige un administrateur AAL2.
function renderSafeAnalyticsTable(node, entries) {
  if (!node) return;
  const rows = entries.length ? entries : [['Aucune donnée', null]];
  const elements = rows.map(([label, count]) => {
    const row = document.createElement('tr');
    const name = document.createElement('td');
    name.textContent = String(label ?? '');
    if (count === null) {
      name.colSpan = 2;
    } else {
      const value = document.createElement('td');
      value.textContent = String(count ?? '');
      row.appendChild(name);
      row.appendChild(value);
      return row;
    }
    row.appendChild(name);
    return row;
  });
  node.replaceChildren(...elements);
}

async function init() {
  if (!isSinjiraBackendConfigured()) {
    setStatus(status, 'Configurez Supabase avant d’utiliser l’analyse SINJIRA.', 'error');
    return;
  }

  try {
    await requireUser('/compte/connexion.html');
    const supabase = getSupabase();
    const { data, error } = await supabase.functions.invoke('admin-analytics', {
      body: { game_slug: 'fracture-du-reseau-mere' }
    });

    if (error || !data?.ok) {
      setStatus(status, data?.error || error?.message || 'Accès administrateur refusé.', 'error');
      return;
    }

    const a = data.analytics;
    renderCard('[data-total-contributions]', a.total_contributions);
    renderCard('[data-average-players]', a.average_player_count ?? '—');
    renderCard('[data-average-duration]', a.average_duration_minutes ? `${a.average_duration_minutes} min` : '—');
    renderCard('[data-average-rating]', a.average_rating ? `${a.average_rating}/5` : '—');

    const results = document.querySelector('[data-result-table]');
    renderSafeAnalyticsTable(results, Object.entries(a.results || {})
      .sort((x, y) => Number(y[1]) - Number(x[1]))
      .map(([label, count]) => [label || 'Non indiqué', count]));

    const difficulty = document.querySelector('[data-difficulty-table]');
    renderSafeAnalyticsTable(difficulty, Object.entries(a.difficulty || {})
      .sort((x, y) => Number(y[1]) - Number(x[1]))
      .map(([label, count]) => [label || 'Non indiqué', count]));

    const cards = document.querySelector('[data-card-table]');
    renderSafeAnalyticsTable(cards, (Array.isArray(a.top_cards) ? a.top_cards : [])
      .map((item) => [item?.card ?? '', item?.count ?? '']));

    setStatus(status, 'Analyse chargée à partir des contributions volontaires.', 'success');
  } catch (error) {
    if (error?.message !== 'Connexion requise') {
      setStatus(status, error?.message || 'Erreur de chargement.', 'error');
    }
  }
}

init();
