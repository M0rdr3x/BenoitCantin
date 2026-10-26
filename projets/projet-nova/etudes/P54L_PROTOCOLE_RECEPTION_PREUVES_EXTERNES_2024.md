# P54L — Réception de pièces liées aux vérifications professionnelles externes

**Projet Nova — 24 octobre 2026.** Le programme prépare la conservation de pièces éventuelles; il ne consulte aucun registre professionnel, ne contacte aucun expert et ne demande aucune authentification de signature.

## Point de départ

[P54K, GitHub Actions #40138509391](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40138509391) s'est terminé avec succès : 75 tests. Les quatre dossiers P54E sont ouverts; aucun avis signé n'a été authentifié et les 96 contrôles P54B ainsi que les huit contrôles P54C restent non instruits.

La chaîne de référence est P54I (réception documentaire), P54J (avis et réserves déclarés), P54K (double grille de vérification humaine non certifiante), puis P54L (inventaire privé des pièces qui pourraient permettre une authentification future).

## Ce que le système vérifie et ne vérifie pas

Le système vérifie les empreintes des trois fiches P54I, P54J, P54K, la cohérence des mandats et dossiers, l'existence d'une déclaration P54K compatible et l'empreinte SHA-256 **recalculée sur les octets des pièces locales**. Il exige des chemins strictement situés sous un dossier privé preuves, sans lien symbolique ni traversée, et des permissions de fichier non publiques.

Le système ne vérifie **ni l'origine officielle du fichier, ni l'identité civile, ni l'inscription ou le permis professionnel, ni l'authenticité d'une signature, ni l'indépendance juridique**. L'existence d'une pièce locale, même parfaitement hachée, ne constitue aucune certification.

Aucun élément sensible (nom, permis, signature, chemin privé, texte source, identifiant de pièce ou empreinte des preuves privées) n'est émis dans les bilans publics. L'original et la fiche restent intégralement hors Git et GitHub Actions.

## Les quatre catégories documentaires

| Catégorie | Question réservée à une personne habilitée |
|---|---|
| TABLEAU_PROFESSIONNEL | L'identité et le titre ont-ils réellement été vérifiés auprès de l'ordre? |
| AUTHENTICITE_SIGNATURE | L'original et la signature ont-ils été authentifiés par la procédure applicable? |
| CONFLITS_D_INTERETS | Les liens et conflits réels, apparents ou potentiels ont-ils été examinés? |
| VALIDITE_MANDAT | La mission était-elle consentie, signée et limitée à la bonne portée? |

Le dossier local peut déclarer « à vérifier », « pièce locale non authentifiée », « réserve explicite » ou « suspension explicite ». Aucun champ ne permet de déclarer que la certification existe; les indicateurs de vérification officielle doivent rester strictement faux.

La priorité des décisions demeure **suspension**, puis **contradiction non résolue**, puis **réserve**, puis **fichier local nécessitant authentification**, et enfin **absence de pièce**. Les alertes P54K et P54J ne disparaissent pas parce qu'un nouveau fichier est ajouté.

Une preuve n'est comptabilisée que si elle est associée à une observation précise, un dossier P54E, un mandat et une catégorie. La réutilisation de la même pièce pour deux prétendues preuves distinctes est rejetée.

## Sources professionnelles pour examen humain seulement

- [Barreau du Québec — vérifier le statut de l'avocat](https://www.barreau.qc.ca/fr/grand-public/faire-affaire-avec-un-avocat/verification-statut-avocat/).
- [Ordre des CPA du Québec — tableau des membres](https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/).
- [Ordre des CPA du Québec — conflits d'intérêts](https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/).

Ces liens orientent un véritable examen professionnel. Ils ne signifient pas qu'une vérification a été effectuée pour le Projet Nova.

## Commandes

Créer un bilan neutre sans personne ni document :

    python scripts/recevoir_preuves_externes_nova_p54l.py --bilan p54l_public_neutre.json

Créer une fiche privée avec les trois sources P54I/P54J/P54K effectivement présentes :

    python scripts/recevoir_preuves_externes_nova_p54l.py --p54i /espace_prive/p54i.json --p54j /espace_prive/p54j.json --p54k /espace_prive/p54k.json --modele-prive /espace_prive/p54l.json

La fiche privée contient un tableau pieces conforme au vocabulaire fermé de P54F (type autorisé : PIECE_JUSTIFICATIVE_PRIVEE) et un tableau observations. Chaque observation inclut dossier_id, mandat, categorie, qualification_declaree et piece_referencee (ID de la pièce sous preuves/). Une observation « PIECE_LOCALE_NON_AUTHENTIFIEE » exige une pièce réelle, hachée et distincte; une suspension peut être déclarée sans fichier.

Analyser les pièces sans diffuser les originaux :

    python scripts/recevoir_preuves_externes_nova_p54l.py --p54i /espace_prive/p54i.json --p54j /espace_prive/p54j.json --p54k /espace_prive/p54k.json --pieces-locales /espace_prive/p54l.json --bilan p54l_bilan_agrege.json

Vérifier le refus d'une certification automatique :

    python scripts/recevoir_preuves_externes_nova_p54l.py --exiger-authenticite

Codes 0 : cohérence de structure et d'empreinte uniquement; 2 : refus du dossier ou de la provenance déclarée; 3 : impossibilité de certifier automatiquement. **Aucun code n'équivaut à une validation professionnelle.**

## Verrous institutionnels

P54L ne permet aucune attribution de marché public, aucun mandat effectif, aucune consultation d'ordre, aucune sortie de fonds, aucune décision de modification budgétaire ni de constitution. Les écritures Ville–RTC déjà éliminées en consolidation ne sont pas transformées en nouvelles économies. Les deux régimes constitutionnels restent séparés; la continuité des emplois et services est maintenue.

**NO_GO_AUTOMATIQUE : zéro vérification officielle réalisée, zéro avis authentifié, zéro économie certifiée; aucune fusion dans main ni opération SINJIRA.**
