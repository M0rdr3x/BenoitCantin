import {getSupabase, isSinjiraBackendConfigured, setStatus, SINJIRA_CONFIG} from './sinjira-supabase.js';

// Cette page ne consomme JAMAIS un jeton pendant son chargement.
// Le POST verifyOtp est déclenché exclusivement par le clic de la personne.
// Le jeton est reçu dans le fragment (#), pour éviter son envoi au serveur Web.
const status = document.querySelector('[data-confirm-status]');
const confirmButton = document.querySelector('[data-confirm-button]');
const nextLink = document.querySelector('[data-confirm-next]');
const resendForm = document.querySelector('[data-confirm-resend-form]');
const resendStatus = document.querySelector('[data-resend-status]');
const resendButton = resendForm?.querySelector('button[type="submit"]');
const fragment = new URLSearchParams(location.hash.replace(/^#/, ''));
const tokenHash = String(fragment.get('token_hash') || '').trim();
const tokenType = String(fragment.get('type') || 'email').trim();

async function notifyAccountConfirmation() {
  try {
    // Avis anonymisé, dédoublonné côté serveur; ce canal ne gère pas les comptes.
    await getSupabase().functions.invoke('notify-account-confirmation',{body:{},signal:AbortSignal.timeout(8500)});
  } catch {
    // L'authentification réussie ne dépend jamais de Formspree.
  }
}
function showSuccess(user) {
  const questionnaire = user?.user_metadata?.wants_character_questionnaire === true;
  nextLink.href = questionnaire ? '/projets/sinjira/registre/' : '/compte/index.html';
  nextLink.textContent = questionnaire ? 'Ouvrir mon questionnaire' : 'Accéder à mon compte';
  nextLink.hidden = false;
  confirmButton.hidden = true;
  setStatus(status, 'Votre courriel est confirmé. Votre Compte SINJIRA™ est maintenant prêt.', 'success');
}

async function init() {
  if (!isSinjiraBackendConfigured()) {
    setStatus(status, 'Le service de comptes est temporairement indisponible.', 'error');
    return;
  }
  if (tokenHash) {
    if (!['email', 'signup'].includes(tokenType)) {
      setStatus(status, 'Ce type de lien n’est pas pris en charge sur cette page.', 'error');
      return;
    }
    confirmButton.hidden = false;
    setStatus(status, 'Le lien est prêt. Cliquez sur « Confirmer mon compte » pour terminer votre inscription.');
    return;
  }
  try {
    const {data, error} = await getSupabase().auth.getUser();
    if (!error && data?.user?.email_confirmed_at) {
      await notifyAccountConfirmation();
      showSuccess(data.user);
      return;
    }
  } catch {
    // Un lien périmé ou manquant doit simplement permettre une nouvelle demande.
  }
  setStatus(status, 'Aucun code de confirmation valide n’est présent dans ce lien. Demandez un nouveau courriel ci-dessous.', 'error');
}

confirmButton?.addEventListener('click', async () => {
  if (!tokenHash || confirmButton.disabled) return;
  confirmButton.disabled = true;
  setStatus(status, 'Vérification de votre adresse courriel…');
  try {
    const {data, error} = await getSupabase().auth.verifyOtp({
      token_hash: tokenHash,
      type: 'email'
    });
    if (error) throw error;
    // Ne laissez pas le jeton dans la barre d’adresse après l’échange.
    history.replaceState(history.state, '', location.pathname);
    // La confirmation doit rester valide même si Formspree est indisponible.
    // Attendre la réponse du serveur avant de proposer une navigation, pour
    // éviter qu'un changement de page annule l'envoi de notification.
    await notifyAccountConfirmation();
    showSuccess(data?.user || null);
  } catch {
    setStatus(status, 'Ce lien est invalide, déjà utilisé ou expiré. Demandez un nouveau courriel de confirmation ci-dessous.', 'error');
    confirmButton.hidden = true;
  } finally {
    confirmButton.disabled = false;
  }
});

resendForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!resendForm.reportValidity()) return;
  const email = String(new FormData(resendForm).get('email') || '').trim();
  const submitButton = resendForm.querySelector('[type="submit"]');
  if (submitButton) submitButton.disabled = true;
  try {
    const {error} = await getSupabase().auth.resend({type: 'signup', email, options:{emailRedirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/confirmer.html`}});
    if (error) throw error;
    setStatus(resendStatus, 'Si cette adresse correspond à un compte en attente de validation, un nouveau courriel a été demandé. Vérifiez également vos pourriels.', 'success');
  } catch {
    setStatus(resendStatus, 'Le renvoi est indisponible pour le moment ou la limite d’envoi est atteinte. Réessayez plus tard.', 'error');
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
});

// Le formulaire HTML est bloqué par défaut : seule la logique Supabase est autorisée.
if(resendButton)resendButton.disabled=!isSinjiraBackendConfigured();
init();
