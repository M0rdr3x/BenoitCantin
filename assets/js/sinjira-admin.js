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
    if (results) {
      results.innerHTML = Object.entries(a.results || {})
        .sort((x, y) => y[1] - x[1])
        .map(([label, count]) => `<tr><td>${label || 'Non indiqué'}</td><td>${count}</td></tr>`)
        .join('') || '<tr><td colspan="2">Aucune donnée</td></tr>';
    }

    const difficulty = document.querySelector('[data-difficulty-table]');
    if (difficulty) {
      difficulty.innerHTML = Object.entries(a.difficulty || {})
        .sort((x, y) => y[1] - x[1])
        .map(([label, count]) => `<tr><td>${label || 'Non indiqué'}</td><td>${count}</td></tr>`)
        .join('') || '<tr><td colspan="2">Aucune donnée</td></tr>';
    }

    const cards = document.querySelector('[data-card-table]');
    if (cards) {
      cards.innerHTML = (a.top_cards || [])
        .map((item) => `<tr><td>${item.card}</td><td>${item.count}</td></tr>`)
        .join('') || '<tr><td colspan="2">Aucune donnée</td></tr>';
    }

    setStatus(status, 'Analyse chargée à partir des contributions volontaires.', 'success');
  } catch (error) {
    if (error?.message !== 'Connexion requise') {
      setStatus(status, error?.message || 'Erreur de chargement.', 'error');
    }
  }
}

init();
