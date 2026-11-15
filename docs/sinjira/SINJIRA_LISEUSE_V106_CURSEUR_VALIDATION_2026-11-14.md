# SINJIRA — V106 : navigation par curseur tactile avec une seule confirmation

**14 novembre 2026 — PR #1000 ouverte en brouillon — NO-GO production.**

## Problème corrigé

Dans la V104/V105, la commande mobile **« Aller à l’écran »** déclenchait directement `scrollToScreen(...,{userInitiated:true})` pour chaque événement `input` du curseur. Un seul glissement du doigt produit souvent de nombreux événements `input`. Cela risquait donc de multiplier les déplacements, les notifications de progression et les opérations de sauvegarde locale/cloud prévues par le moteur existant, tout en déclenchant des recalculs de mise en page inutiles.

## Fonctionnement V106

- **Pendant le déplacement du doigt**, seul le pouce du curseur et sa description accessible sont mis à jour : par exemple « Écran 3 sur 8 · page 4 du livre · relâcher pour lire cet écran ». La page du roman, le `scrollTop`, l'annonce `aria-live` et le mécanisme de sauvegarde existant ne sont pas modifiés à chaque position intermédiaire.
- **Au relâchement du curseur** (`change` HTML natif), une seule navigation vers l'écran sélectionné est effectuée. C'est alors seulement que la routine canonique `scrollToScreen(...,{userInitiated:true})` émet le signal existant de progression. Une confirmation du **même écran courant** ne déclenche aucun signal supplémentaire.
- Les valeurs hors bornes, modes PDF et texte continu, pages d'un seul écran et lectures masquées ne changent aucune page.
- Les anciens gestes gauche/droite, les tapotements de marge, la lecture PDF, le texte adaptable, la position locale, les droits d'accès et la synchronisation conditionnelle avec serveur sont préservés.
- Un swipe manuel, un changement de page PDF ou de mode et un redimensionnement annulent une prévisualisation obsolète.

## Modifications GitHub

- `assets/js/sinjira-liseuse-reflow-v53.mjs` : `jumpPreview` temporaire en mémoire, gestion séparée `input` (prévisualisation accessible sans capture d'ancre ni scroll) et `change` (déplacement confirmé), prévention des repositionnements et du signal de progression en double, nettoyage des écouteurs d'événements.
- `compte/liseuse.html` : texte d'aide expliquant le relâchement et version de cache `53.11.14.106`.
- `tests/sinjira-liseuse-reflow-v53.test.mjs` : quatre entrées de prévisualisation ne changent ni la position ni la page et ne provoquent aucune notification de progression; un seul `change` confirme un saut. Relâcher sur la même position ne produit aucun signal. Un swipe réel annule la prévisualisation.
- `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : sur la vraie page HTML, avec PDF fictif et comptes bloqués, quatre changements intermédiaires ne produisent aucun `reader-screen-turn`, puis exactement un événement lors de chaque confirmation. Vérifications Chromium et WebKit.
- `tests/e2e/fixtures/sinjira-liseuse-mobile-v54.html` et test responsive V58 mis en correspondance avec la version V106.

## Validation et limites

La validation exige **tous les workflows applicables réussis sur le SHA HEAD exact**. L'environnement Playwright simule la navigation tactile dans Chromium/WebKit ; il ne remplace pas une homologation sur téléphones physiques iOS/Android ni avec VoiceOver/TalkBack. Les autorisations authentifiées des livres privés et la synchronisation multi-appareils CAS/RLS demandent une validation séparée.

**PR en brouillon, non fusionnée, non déployée** : 13/13 conditions de lancement de SINJIRA restent ouvertes. Aucune certification générale « 100 % sécurisée » ou publication n'est annoncée.

## Avancement global inchangé (bilan de référence du 8 novembre 2026)

| Programme | Avancement documenté | Date de fin |
|---|---:|---|
| Projet Nova — programme politique | **47 %** | **31 décembre 2027**, cible conditionnelle avec report possible en 2028+ |
| Projet Nova–Sinjira — services publics | Aucun pourcentage global défendable, 14 secteurs recensés | Indéterminée |
| Projet Nova — sondage citoyen | **54,5 %**, 6 critères sur 11 | Indéterminée |
| Projet Nova — boussole électorale | **75 %**, 9 critères sur 12 | Indéterminée |
| SINJIRA — plateforme complète | **66,5 % ±10 points**, 13 conditions ouvertes | Indéterminée |

Un correctif local de la liseuse ne justifie aucune augmentation automatique des taux globaux.
