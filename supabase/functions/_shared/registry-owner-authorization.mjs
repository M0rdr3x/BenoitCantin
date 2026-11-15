/**
 * Frontière d'autorisation réservée au propriétaire du Registre.
 * Jamais de privilège dérivé d'un courriel, pseudonyme ou claims modifiables.
 * L'identité UUID est celle du JWT vérifié par requiredVaultUser (AAL2).
 *
 * La fonction is_sinjira_owner s'appuie sur public.internal_admin_users :
 * elle ne reconnaît que le rôle 'owner' pour le compte vérifié.
 */
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function isVerifiedRegistryOwner(service, verifiedUserId) {
  if (typeof verifiedUserId !== 'string' || !UUID_RE.test(verifiedUserId)) {
    throw new Error('REGISTRY_OWNER_CHECK_FAILED');
  }
  try {
    if (!service || typeof service.rpc !== 'function') {
      throw new Error('REGISTRY_OWNER_CHECK_FAILED');
    }
    const {data,error} = await service.rpc('is_sinjira_owner',{p_user_id:verifiedUserId});
    // false signifie « rôle non propriétaire »; tout autre état est indéterminé.
    if (error || (data !== true && data !== false)) {
      throw new Error('REGISTRY_OWNER_CHECK_FAILED');
    }
    return data === true;
  } catch {
    // Ne jamais révéler le message backend ni autoriser un repli par courriel.
    throw new Error('REGISTRY_OWNER_CHECK_FAILED');
  }
}
