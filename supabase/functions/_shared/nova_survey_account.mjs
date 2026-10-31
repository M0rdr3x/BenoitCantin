// Pré-validation de l'identité de l'auteur d'un sondage politique Nova.
// Supabase Auth délivre aussi des sessions au rôle "authenticated" pour les
// comptes anonymes ; seule une identité permanente peut être admise ici.
// Cette vérification porte sur le user retourné par getUser() CÔTÉ SERVEUR.
// Elle ne constitue pas une preuve d'une personne unique ni de sa majorité.
export function isPermanentNovaSurveyAccount(user) {
  return user !== null &&
    typeof user === 'object' &&
    typeof user.id === 'string' &&
    user.id.length > 0 &&
    user.is_anonymous === false;
}
