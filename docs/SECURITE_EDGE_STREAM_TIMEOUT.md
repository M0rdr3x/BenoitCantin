# Sécurité Edge — délais bornés pour les flux de requêtes

## Risque observé dans le code GitHub

Le lecteur partagé `supabase/functions/_shared/limited-body.mjs` plafonnait
correctement la taille et validait UTF-8 strict, mais attendait
`reader.read()` sans délai global ni réaction explicite à l'abandon de
`Request.signal`. Un client transmettant un préfixe puis restant connecté
pouvait prolonger inutilement une invocation. Ce risque de disponibilité
ne prouve aucune attaque réelle.

La fonction `send-game-report`, ouverte aux téléchargements anonymes,
télécharge également un modèle PDF. Le code GitHub ne bornait pas la durée
totale de son appel `fetch()`, même si la lecture binaire est limitée
en octets.

## Mesures préparées

- Le lecteur UTF-8 partagé conserve ses limites de taille, de
  `Content-Length` et d'encodage, mais borne désormais la durée totale
  de réception à **20 secondes** par défaut.
- Les signaux d'abandon clients interrompent la lecture. L'annulation du
  flux est lancée sans attendre indéfiniment le producteur (`cancel()`
  peut retourner une promesse qui ne se termine pas).
- Une réponse partielle après délai ou abandon est refusée entièrement :
  aucune portion ne peut être traitée comme un JSON accepté.
- L'appel au modèle PDF est assorti de
  `AbortSignal.timeout(15_000)`; le plafond binaire de 15 Mio et
  le refus des redirections demeurent actifs.
- Les tests Node exécutent des flux synthétiques qui s'interrompent,
  ne se terminent jamais et refusent d'achever `cancel()`.
  Le garde CI existant des fonctions publiques lance ces tests.

## Vérifications et décisions de publication

1. Exiger la CI verte sur le SHA exact de la PR et la revue des
   changements du helper partagé.
2. Tester en staging les téléchargements légitimes de la fiche joueur,
   les limites de connexions lentes et les cas 413, sans compte ni PDF réel.
3. Vérifier séparément les versions déployées ; **un commit GitHub ne
   met pas à jour les Edge Functions actives**.
4. Conserver les exceptions `verify_jwt=false` explicitement approuvées
   et l'inventaire de déploiement en quarantaine (#702, #759).
5. Prévoir une procédure de retour arrière avant tout déploiement
   ciblé approuvé.

Cette correction **ne limite pas la fréquence ni la concurrence des
générations de PDF**. La limitation distribuée, les quotas et les
protections WAF restent à réaliser dans le ticket #704.

Aucune migration SQL, configuration Auth, clé, donnée personnelle,
fonction de production ou service payant n'a été modifié ici.
