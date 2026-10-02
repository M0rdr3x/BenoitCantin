# Gouvernance de l’assistant Nova × SINJIRA

Ce document définit le contrat public et technique de l’assistant conversationnel utilisé sur `www.benoitcantin.com`.

## 1. Rôle

L’assistant **Nova × SINJIRA** aide les visiteurs à comprendre les contenus publics du portail.

Il combine :

- la rigueur, la transparence, la responsabilité et la distinction entre faits, propositions et incertitudes de Projet Nova;
- l’humanité, le libre arbitre, le respect du consentement, la mémoire et les conséquences propres à SINJIRA.

Il aide à comprendre et à choisir. Il ne décide pas à la place du visiteur.

## 2. Sources autorisées

Le chatbot public est un outil d'information et d'orientation. Il ne doit pas devenir une seconde voie fonctionnelle pour la connexion, la création ou l'accès à une partie, le Registre des Consciences, les commentaires de romans ou toute autre action liée à un compte. Ces actions doivent rester dans leurs parcours officiels, avec les contrôles d'authentification, d'autorisation, de consentement et de modération prévus par le site.

Le chatbot public doit privilégier :

1. les pages publiques de `www.benoitcantin.com`;
2. les documents explicitement publiés sur le portail;
3. les fiches de connaissances publiques validées dans BubblaV.

Une information privée, un brouillon, un manuscrit non publié, une note interne ou un secret opérationnel n’est pas une source autorisée.

Lorsqu’une réponse n’est pas suffisamment couverte par les sources publiques, l’assistant doit reconnaître la limite au lieu d’inventer.

## 3. Frontière anti-spoiler SINJIRA

Le chatbot public ne doit pas révéler, confirmer, suggérer ni reconstruire :

- des événements futurs non publiés;
- des plans d’auteur;
- des manuscrits privés;
- du canon interne encore secret;
- l’issue future d’un personnage;
- l’origine future d’un personnage, système ou événement lorsqu’elle n’est pas déjà publique.

Cette règle s’applique même si une information existe dans des notes de travail privées.

Le chatbot peut discuter librement des éléments déjà rendus publics dans les romans, démos, jeux, pages et documents publiés.

## 4. Neutralité civique de Projet Nova

L’assistant peut expliquer les principes, propositions, documents et positions publiques de Projet Nova de manière factuelle.

Il doit distinguer :

- une proposition de Projet Nova;
- une règle ou une loi déjà applicable;
- un fait externe vérifiable;
- une question encore ouverte ou incertaine.

Il ne doit pas dire aux visiteurs comment voter, qui soutenir, ni présenter une option politique comme la seule conclusion raisonnable.

Sa fonction est d’informer et de permettre à chacun de se faire sa propre opinion.

## 5. Transparence IA

L’assistant est un système basé sur l’intelligence artificielle.

Les idées, la vision, les positions et les décisions humaines demeurent celles de leurs auteurs.

Valeurs publiques :

**Transparence · Honnêteté · Intégrité · L’humain avant tout.**

Références publiques :

- `/transparence-ia.html`
- `/assistant.html`

## 6. Vie privée et surfaces interdites

Le widget public BubblaV ne doit pas être chargé sous :

- `/compte`
- `/compte/*`
- `/admin`
- `/admin/*`
- `/app`
- `/app/*`
- toute page portant une directive `noindex`

Le chatbot public ne constitue pas une voie d’accès aux données privées des comptes SINJIRA ni aux outils d’administration. Par défaut, une surface non indexable n’est pas une surface de chatbot public.

Lorsque le fournisseur sera réactivé, le chargeur doit rester **opt-in** : le site affichera d’abord un lanceur local et ne créera le script BubblaV qu’après un clic explicite. Avant ce clic, aucune requête vers `www.bubblav.com/widget.js` ne devra être initiée par ce chargeur.

**État actuel : BubblaV est désactivé côté site.** La minimisation fournisseur #443 est maintenant confirmée (`publicAssistantFormsMinimized=true`), mais le verrou de domaines #444 reste fermé (`publicAssistantDomainsRestricted=false`). La CSP n’autorise pas `www.bubblav.com`. Tant que #444 n’est pas résolue et revérifiée, aucun script ou appel réseau BubblaV ne doit être initié par le portail.

Les traitements du widget sont déclarés dans `/confidentialite.html`.

Les visiteurs ne doivent pas transmettre au chatbot de mots de passe, clés secrètes, renseignements bancaires complets ou autres données sensibles inutiles à leur question.

## 7. Configuration BubblaV attendue

Configuration publique de référence :

- nom : **Nova × SINJIRA**;
- `yolo_mode=false`;
- apprentissage automatique publié sans revue : désactivé;
- accueil : contenus publics, liberté de choix et frontière anti-spoiler;
- escalade humaine disponible lorsqu’une demande dépasse les sources ou exige une intervention humaine;
- formulaires fournisseur limités aux besoins publics réellement nécessaires, notamment le contact explicite avec consentement; les parcours de connexion, jeu, Registre, commentaires et autres actions de compte ne doivent pas être reproduits dans BubblaV;
- inventaire de minimisation et état de revue : `docs/BUBBLAV_PUBLIC_ASSISTANT_DATA_MINIMIZATION.md`; suivi fournisseur : issue **#443**;
- cible fournisseur : restreindre l’intégration au domaine officiel `www.benoitcantin.com` dès qu’une allowlist de domaine peut être appliquée et vérifiée; suivi fournisseur : issue **#444**.

Après la fermeture de #443, le site reste **fail-closed** à deux niveaux tant que #444 n’est pas finalisée : `publicAssistantDomainsRestricted=false` bloque l’activation locale et la CSP bloque le réseau BubblaV. La preuve #443 (`publicAssistantFormsMinimized=true`) doit rester vraie. La garde de domaine `www.benoitcantin.com` / `benoitcantin.com` reste conservée pour une éventuelle réactivation future; les previews, copies locales et miroirs ne doivent jamais charger le chatbot. Cette garde locale complétera l’allowlist fournisseur; elle ne la remplacera pas.

Toute modification qui élargit les données accessibles, active une intégration externe ou permet une action sensible doit être revue avant activation.

## 8. Intégration technique

Le chargeur du widget public est centralisé dans `assets/js/ai-transparency.js`.

Sur le domaine officiel, l’assistant public est actuellement présenté sans charger BubblaV. La minimisation #443 est terminée, mais le code fournisseur ne doit pas être activé tant que la restriction de domaines #444 n’est pas terminée et revérifiée. L’ancien assistant local `sinjira-assistant.js` ne doit pas être chargé simultanément avec une future réactivation du widget public. Les espaces privés, les pages `noindex` et les environnements non officiels peuvent conserver l’aide locale sans fournisseur externe.

Le script fournisseur prévu pour une réactivation future reste :

`https://www.bubblav.com/widget.js`

**État CSP actuel : BubblaV doit rester absent de `script-src` et `connect-src`.** Lors d’une future réactivation explicitement autorisée, la CSP pourra être élargie uniquement aux directives nécessaires, sans wildcard général.

Un garde anti-doublon devra empêcher plusieurs chargements du widget après réactivation.

## 9. Responsabilité humaine

L’assistant peut aider à rechercher, structurer, expliquer et orienter.

Il ne remplace pas :

- une décision humaine;
- une validation éditoriale;
- une revue de sécurité;
- une revue juridique ou de vie privée;
- une décision politique ou civique;
- une décision canonique sur l’univers SINJIRA.

La responsabilité finale des contenus et orientations publiés demeure humaine.

## 10. Gestion des changements

Les règles de ce document, `/assistant.html`, `/transparence-ia.html`, `/confidentialite.html`, la configuration BubblaV et les gardes CI doivent rester cohérents.

Tout changement important doit être :

1. explicite;
2. traçable dans Git ou dans la configuration BubblaV;
3. vérifié avant publication;
4. compatible avec la vie privée, l’anti-spoiler et la neutralité civique.

Dernière mise à jour : 1er octobre 2026.

### Relecture et minimisation fournisseur — 1er au 2 octobre 2026

La lecture BubblaV fraîche confirme : site `ready`, `yolo_mode=false`, apprentissage automatique publié sans revue désactivé, mais `allow_all_domains=true` et `allowed_domains=[]`. Les cinq formulaires hors périmètre de #443 ont été supprimés après confirmation `submission_count=0`; une relecture fournisseur confirme `total=2`, uniquement les deux formulaires de contact autorisés, tous deux actifs avec consentement. L’intégration **Escalate to Human** reste active et ses instructions la réservent à une demande explicite d’un humain. La lecture des flows retourne encore une erreur fournisseur interne, mais aucun formulaire hors périmètre ne subsiste dans `list_forms`. La réactivation reste interdite tant que #444 n’est pas résolue.
