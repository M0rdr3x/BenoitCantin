# Projet Nova — P52T : comparaison de deux acquisitions distinctes des PDF officiels

**20 octobre 2026 — étude technique non adoptée.**

## Finalité

P52S a effectivement reçu deux PDF budgétaires publics par HTTPS, calculé leurs empreintes SHA-256 et répété le transfert avec succès. P52T améliore cette méthode : **deux jobs GitHub Actions distincts** téléchargent les mêmes sources à partir d'URL strictement contrôlées, puis un troisième job compare les deux reçus et les deux références historiques de P52S.

Les deux captures proviennent de la même plateforme, du même code et des mêmes URL. L'indépendance est **technique et partielle**, non humaine, juridique ou institutionnelle. Des jobs différents ne prouvent pas l'utilisation d'hôtes physiques distincts. Le contrôle TLS standard ne constitue pas une signature du ministère.

## Décisions techniques et protocoles

- `IDENTIQUE_3_REFERENCES` : les octets de A, B et P52S ont même taille et SHA-256; aucune preuve F09 authentifiée n'en découle.
- `DIVERGENCE_ENTRE_TACHES` : les octets de A et B ne correspondent pas; le workflow s'arrête sans réécrire les empreintes historiques.
- `DERIVE_DEPUIS_P52S` : A et B concordent, mais diffèrent de P52S; possible mise à jour ou incident. Un humain doit examiner la nouvelle version.
- `CAPTURE_MANQUANTE` : échec de récupération dans au moins un des deux jobs; aucune conclusion favorable.

Le résultat du comparateur retourne le code **0** uniquement pour la cohérence technique. Le code **4** signale un écart ou un téléchargement manquant en mode strict; **2** signale des métadonnées ou reçus incohérents; **3** indique qu'aucune expertise humaine n'est obtenue malgré un éventuel rapprochement réussi. Dans tous les cas, le verdict institutionnel est **NO_GO_AUTOMATIQUE**.

Les deux jobs utilisent `permissions: contents: read`, un checkout sans authentifiants persistants et la vérification HTTPS de P52S. Ils ne téléchargent que les deux URL exactes du ministère, refusent les redirections et limitent les fichiers à 50 Mo. Le flux PDF ne quitte pas la mémoire du programme; seuls les reçus de tailles, empreintes, dates, identifiants de job et statuts sont conservés temporairement dans GitHub Actions. Aucun PDF, pièce personnelle ni signature n'est déposé.

## Utilisation

```bash
# Validation du schéma et des preuves P52S/P52K/P52A (aucun réseau)
python scripts/controler_double_capture_nova_p52t.py audit

# Les jobs GitHub exécutent ceci après leur capture P52S
python scripts/controler_double_capture_nova_p52t.py envelopper --role A --capture capture.json --sortie recu-a.json

# Comparaison des deux tâches et du relevé historique
python scripts/controler_double_capture_nova_p52t.py comparer --a recu-a.json --b recu-b.json --exiger-coherence --rapport decision.json
```

`envelopper` exige les variables `NOVA_RUN_ID`, `NOVA_RUN_ATTEMPT`, `NOVA_SHA`, `NOVA_JOB` et `NOVA_RUNNER_OS`. Elles ne prouvent pas, à elles seules, qu'un tiers indépendant a vérifié l'exécution; elles permettent surtout de détecter qu'on compare des jobs d'exécutions différentes. Les tests unitaires utilisent uniquement des échantillons synthétiques, aucun accès Internet.

## Contrôle institutionnel toujours manquant

F09 nécessite encore des copies licites archivées hors GitHub, la vérification de l'édition réelle et des pages, une seconde lecture **humaine indépendante** et un avis signé, avec déclaration des conflits et réserves. Les **20 exigences F01–F20** demeurent bloquantes et les **1 320 valeurs financières** inconnues. Les deux régimes du projet (Québec au Canada / Québec souverain hypothétique) ne peuvent pas être certifiés par des empreintes PDF.

PR #673 reste en brouillon. Protection de `main` (#135) et revue humaine indépendante (#662) restent préalables à toute fusion. Ne pas modifier SINJIRA.
