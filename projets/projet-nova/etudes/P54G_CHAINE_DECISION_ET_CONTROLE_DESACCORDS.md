# P54G — Registre des décisions de suivi, sans clôture automatique

**Projet Nova — 24 octobre 2026.** Le jalon P54G s'appuie sur les quatre occurrences indéterminées P54D, la préparation des dossiers P54E et le protocole de contre-revue P54F. Aucune analyse comptable indépendante signée n'est obtenue par le seul logiciel.

## Motivation

Les 4 dossiers P54E (P54E-V-001, P54E-M-001/002/003) doivent rester ouverts tant que les responsables n'ont pas examiné les documents originaux, distingué pagination/références/rubriques comptables, déterminé unités et périmètres, résolu les contradictions et vérifié les responsabilités professionnelles.

P54F reçoit au maximum deux déclarations de rôle par dossier et distingue les situations de suspension, désaccord, revue unilatérale, concordance déclarative complète ou incomplète. **Ces statuts décrivent la procédure et ne prouvent ni l'identité ni la qualification réelle des intervenants.** P54G peut prendre acte de cette situation, mais ne doit jamais produire une décision définitive ou une économie validée.

## Transitions autorisées pour le suivi

| État documentaire P54F | Actions de suivi P54G admissibles |
|---|---|
| EN_ATTENTE | AJOURNER; DEMANDER_PIECES |
| EXAMEN_UNIQUE | AJOURNER; DEMANDER_CONTRE_REVUE |
| DESACCORD | AJOURNER; DEMANDER_PIECES; SAISIR_EXPERT_INDEPENDANT |
| SUSPENDU | AJOURNER; MAINTENIR_SUSPENSION |
| CONCORDANCE_DECLARATIVE_INCOMPLETE | AJOURNER; DEMANDER_PIECES; DEMANDER_CONTRE_REVUE |
| CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE | AJOURNER; SAISIR_EXPERT_INDEPENDANT |

**« Saisir un expert » est une orientation déclarée, jamais une preuve que l'expert a réellement été contacté ou mandaté.** Une déclaration « demander des pièces » ne déclenche aucune demande externe. P54G ne contient aucune opération de transmission, aucun vote, aucun changement fiscal, aucun mécanisme de signature numérique officielle, aucun statut GO et aucune action de fusion.

## Contrôles intégrés

La fiche structurée de suivi accepte seulement un identifiant de dossier connu, une action autorisée pour l'état de P54F, un motif dans le vocabulaire fermé et éventuellement des catégories de pièces à solliciter. Les doublons, les catégories absentes ou non admissibles, les demandes sans pièces, les identifiants inattendus et les transitions incompatibles sont refusés.

Quatre champs restent obligatoirement faux : identité vérifiée, avis signé vérifié, clôture financière autorisée et transmission externe effectuée. **Le logiciel ne dispose pas des mécanismes pour authentifier ces actes.** Une tentative de passer l'un de ces champs à vrai est rejetée, et non transformée en événement validé.

Les fichiers de revue, les notes brutes, les empreintes des pièces privées et les éventuelles identités restent dans un emplacement local sécurisé hors GitHub. Le logiciel ne publie que les statuts de dossiers connus et un bilan agrégé. Il refuse les fichiers privés accessibles à d'autres utilisateurs et les modèles privés situés dans le dépôt.

## Utilisation

Produire une synthèse neutre à partir de la configuration, sans donnée privée :

    python scripts/controler_decisions_procedurales_nova_p54g.py --bilan p54g_bilan_vierge.json

Créer le modèle de décisions dans un dossier privé hors GitHub (permissions 0600) :

    python scripts/controler_decisions_procedurales_nova_p54g.py --modele-prive /repertoire_prive/p54g_decisions.json

Après une revue P54F documentée localement, ajouter les décisions de suivi **déclaratives** dans ce modèle, puis produire uniquement le bilan anonymisé :

    python scripts/controler_decisions_procedurales_nova_p54g.py --revues-locales /repertoire_prive/p54f_revues.json --decisions-locales /repertoire_prive/p54g_decisions.json --bilan p54g_suivi_public.json

Refuser explicitement tout GO :

    python scripts/controler_decisions_procedurales_nova_p54g.py --exiger-go

Codes de retour : 0 = format accepté et transition procédurale compatible; 2 = déclaration, source privée ou transition irrecevable; 3 = refus de toute certification automatique. **Même le code 0 n'est pas un avis professionnel ni une autorisation institutionnelle.**

## Points restant hors de portée

Le système n'a ni obtenu de consultation d'expert indépendante, ni rapproché les écritures réciproques Ville–RTC, ni vérifié les quatre occurrences indéterminées par une personne habilitée, ni résolu les 96 contrôles comptables P54B et huit contrôles documentaires P54C. Il conserve l'occurrence classée « date ou année probable » comme hypothèse, sans la transformer en preuve.

Les garanties de maintien des emplois et de continuité des services, l'interdiction du double compte comptable, la prudence fiscale et la séparation des scénarios Québec au Canada / Québec souverain demeurent obligatoires.

**Décision : NO_GO_AUTOMATIQUE. Aucune économie certifiée, aucune réduction autorisée, aucun document privé transmis, aucun merge vers main et aucune action SINJIRA.**
