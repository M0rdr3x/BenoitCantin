# BenoitCantin / SINJIRA — V19 PRO

V19 est une consolidation de qualité et de stabilité basée sur V18 FINAL REV2.

## Améliorations principales
- constellation réellement responsive sur mobile;
- session Compte SINJIRA visible dans la navigation publique;
- PWA / cache hors ligne prudent pour les pages publiques et les règles de Fracture;
- images officielles lourdes servies en WebP optimisé;
- lecteur de la démo avec page mémorisée et progression;
- commentaires avec divulgâcheurs + modification/suppression tant qu’ils sont en attente;
- timeline du Registre dans `Mes personnages`;
- export/import local JSON des parties;
- journal administratif et état du système;
- journalisation des actions sensibles V19;
- garde-fous CANON et verrou Roman 1 conservés;
- nettoyage des fichiers parasites;
- RLS complétée pour les commentaires en attente.

## Backend à appliquer
Exécuter `supabase/migrations/20260812_sinjira_v19_pro.sql`, puis redéployer :
- `submit-character-questionnaire`
- `admin-sinjira-v18`

La génération OpenAI reste facultative et désactivable. Le mode manuel/Formspree continue de fonctionner.
