# SINJIRA V141 — préserver les réglages de liseuse pendant la suspension

**16 novembre 2026 — PR #1000 DRAFT, non déployée.**

## Défaut corrigé

Les V137–V140 bloquaient les changements de page, les sauvegardes, les départs de narration et les commandes de rendu lors du masquage d'un livre. Mais les contrôles de thème, taille, police, interligne, largeur et espacement des caractères pouvaient encore réécrire les préférences locales et modifier le CSS alors que le livre était caché. En outre, le moteur de pagination V53 recevait les événements `input/change` **en phase capture**, avant V26, et pouvait mémoriser une ancre sur un viewport masqué d'une hauteur nulle. Ces événements peuvent provenir de formulaires différés au moment d'un verrouillage, d'un changement d'application ou d'une suspension privée.

## Correction

- La fonction V26 `canEditReaderAppearance(event,current)` réutilise `canRecordReaderInteraction()`. En cas de roman/document masqué ou de droit privé suspendu/révoqué, le champ revient à sa valeur canonique, sans `setTheme()`, sans `savePreferences()`, sans changement du CSS ni extraction du livre.
- Les six champs de présentation concernés sont : `reader-theme`, `reader-size`, `reader-font`, `reader-line-height`, `reader-text-width` et `reader-letter-spacing`.
- V53 refuse `onPreferences` lorsque `canNavigate()` est faux; la capture ne prépare alors pas de restitution d'ancre au viewport masqué.
- Les règles Auth/RLS, les fichiers de roman, les commandes audio indépendantes, les styles des écrans visibles et la sauvegarde légitime de progression ne changent pas.
- Versions de cache **V26 34.11.16.141** et **V53 53.11.16.141**, alignées HTML, contrat Node, fixture et imports de laboratoire.

## Validation automatisée

Dans `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : masquer la vraie zone HTML du livre fictif, simuler les six changements `input/change`, puis comparer les valeurs des contrôles, le thème et les variables CSS, le libellé de taille et le JSON de préférences en localStorage. Aucune de ces valeurs ne doit changer. Les tests existants vérifient ensuite que le curseur de pagination, les gestes et le texte restent opérationnels après réouverture sur Chromium et WebKit.

**CI finale du SHA à vérifier**. La validation physique iPhone/Android, VoiceOver/TalkBack, l'homologation des droits et révocations privés et la synchronisation sur plusieurs appareils restent des conditions de publication. **PR DRAFT / NO-GO**, scores globaux inchangés.
