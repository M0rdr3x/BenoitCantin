# P54F — Protocole de révision contradictoire des quatre dossiers

**24 octobre 2026 — Dossier non certifiant, sans économies démontrées.**

## Ancrages documentaires

P54D a relevé cinq occurrences numériques non appariées sur les PDF 2024 de la Ville de Québec (index PDF 102) et du MAMH (index PDF 162) : une année/date probable et quatre indéterminées. P54E a préparé quatre dossiers : P54E-V-001, P54E-M-001, P54E-M-002 et P54E-M-003. Plusieurs observations MAMH sont situées dans la même zone approximative de fin de page; leur localisation exacte exige les pièces originales.

Sources d'exécution : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40120462237 (P54D) ; https://github.com/M0rdr3x/BenoitCantin/actions/runs/40122050552 (P54E).

## Double revue, jamais double certification

Chaque dossier admet deux rôles déclaratifs : EXAMINATEUR et CONTRE_REVISEUR. Il y a donc huit positions de rôle et quatre-vingts contrôles potentiels (quatre dossiers, deux rôles, dix contrôles hérités de P54E). Un identifiant pseudonyme distinct est obligatoire entre les deux rôles d'un même dossier. Cette condition technique n'authentifie cependant ni l'identité civile, ni le titre comptable, ni l'indépendance réelle.

| Statut du dossier | Sens limité |
|---|---|
| EN_ATTENTE | Aucune déclaration reçue |
| EXAMEN_UNIQUE | Une déclaration de rôle reçue |
| CONCORDANCE_DECLARATIVE_INCOMPLETE | Deux déclarations non contradictoires, sans dossier complet |
| CONCORDANCE_DECLARATIVE_DOCUMENTEE_NON_ATTESTEE | Deux déclarations compatibles, chacune décrivant dix contrôles, et une pièce commune vérifiée par empreinte |
| DESACCORD | Hypothèses/statuts/réserves divergents, ou contradiction non levée |
| SUSPENDU | Une déclaration exige la suspension |

Une concordance ne constitue **jamais une clôture légale, un avis signé ou une économie certifiée**. Un désaccord est conservé comme dossier ouvert. Toute décision comptable ou juridique nécessite un examen professionnel hors système et ses véritables documents originaux.

## Chaîne d'intégrité locale

Le formulaire privé et les pièces de travail ne doivent pas être envoyés à GitHub. Ils résident dans un répertoire privé extérieur au dépôt; les pièces sont placées dans le sous-répertoire preuves, sans lien symbolique ni traversée de dossiers. Le programme exige des permissions privées et contrôle les empreintes SHA-256 en recalculant effectivement le hachage des octets. Maximum douze pièces, trente-deux Mio par pièce, cent vingt-huit Mio cumulés; formulaire de 64 Kio au plus.

Les types de preuve admis sont : publication PDF, note d'analyse privée, pièce justificative privée et avis professionnel NON ATTESTÉ. Une empreinte locale concordante **ne prouve pas la signature ni la provenance officielle d'un document**. Les empreintes des versions de PDF public ancrées dans P53Z/P54D sont vérifiées séparément.

Aucun texte source, nom réel, montant, chemin de fichier, code pseudonyme de relecteur, extrait de page ou empreinte d'une pièce privée n'est publié dans le bilan. Le rapport peut contenir un état procédural par identifiant de dossier connu et des statistiques agrégées uniquement.

## Mode opératoire pour des intervenants habilités

Générer un bilan vierge :

    python scripts/gerer_contre_revues_nova_p54f.py --bilan bilan_p54f.json

Créer un modèle strictement local, hors dépôt, à permissions 0600 :

    python scripts/gerer_contre_revues_nova_p54f.py --modele-prive /repertoire_prive/p54f_revues.json

Compléter les tableaux pieces et revues du modèle, conserver les documents sous /repertoire_prive/preuves/ et inscrire pour chaque pièce un identifiant PIECE-001, le type, le chemin relatif et le SHA-256 exact des octets. Une revue contient un identifiant de dossier P54E, un rôle, un pseudonyme opaque, une hypothèse et un statut du vocabulaire P54E, un état de contradiction, les contrôles déclarés et les IDs des pièces consultées. Les deux champs de certification ou d'avis signé sont obligatoirement false.

Contrôler les pièces locales et générer **seulement un bilan non certifiant** :

    python scripts/gerer_contre_revues_nova_p54f.py --revues-locales /repertoire_prive/p54f_revues.json --bilan p54f_agrege.json

Vérifier qu'une demande de certification aboutit toujours au refus (code 3) :

    python scripts/gerer_contre_revues_nova_p54f.py --exiger-certification

Codes : 0 = dossier structuré accepté ou bilan neutre; 2 = dossier ou preuve irrecevable; 3 = refus de certification automatique. Aucune exécution n'autorise la réduction d'emploi, de services essentiels ou la fusion dans main.

## Questions non résolues et doctrine

Les quatre dossiers ne démontrent encore aucune valeur financière. La cinquième occurrence « année/date probable » demeure provisoire et hors des quatre dossiers. Les 40 points de contrôle P54E, les 96 vérifications P54B et les huit contrôles P54C restent non attestés par le Projet Nova. Les écritures de consolidation Ville–RTC déjà éliminées ne sont jamais comptabilisées comme nouvelles économies.

La double revue locale doit être confrontée aux originaux, aux règles d'accès, aux unités, colonnes, périmètres, états audités ou non, écriture et journaux de contrepartie, puis à une analyse juridique et comptable indépendante signée. Une décision contradictoire non résolue reste NON GO.

Les garanties d'emploi et de continuité des services publics, la séparation du Québec au Canada et du Québec souverain hypothétique et l'indépendance de SINJIRA sont maintenues.

**NO_GO_AUTOMATIQUE — aucun gain certifié, aucune clôture automatique, aucune modification de la branche principale.**
