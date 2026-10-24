# Projet Nova — P53X : comparaison technique des versions officielles Ville / MAMH (2024)

**24 octobre 2026.** Le jalon P53W a établi, par lecture des pages originales du PDF publié par la Ville de Québec, que son rapport financier 2024 décrit le RTC et la SOMHAC dans le périmètre consolidé et précise que les opérations réciproques ont déjà été éliminées (PDF index 34, page imprimée 35). La page imprimée 197 (PDF index 196) est dans une section budgétaire identifiée « Non audité ». Ces observations ne sont pas des économies nouvelles.

**P53X ne prétend pas avoir effectué une comparaison d'octets officiels durant le développement de la PR** : la plateforme de lecture a rendu le PDF municipal consultable, mais la copie ministérielle PDF était trop volumineuse pour son moteur de consultation, et le transfert des deux fichiers vers l'environnement d'exécution local n'a pas réussi. Il serait trompeur d'inventer des hashes, un nombre de pages MAMH, une équivalence, ou des divergences comptables.

## Références d'autorité — et portée

- Ville, rapport financier 2024 : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf
- Répertoire officiel de la Ville : https://www.ville.quebec.qc.ca/apropos/profil-financier/rapport-financier.aspx
- MAMH, diffusion 2024 du dossier 23027 : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf
- MAMH, règle de publication : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier

Le MAMH explique que les rapports transmis et autres renseignements financiers peuvent être **assemblés en un PDF unique**, que l'organisme peut transmettre à nouveau une version corrigée et que le destinataire doit prendre en compte d'éventuelles mises à jour. Deux PDFs ont ainsi des périmètres éditoriaux potentiellement différents; le nombre de pages ou leur ordre ne prouve pas une divergence des comptes.

## Programme de contrôle

Un outil local, sans requête réseau, effectue quatre contrôles seulement après la fourniture volontaire des deux PDFs :

1. **Identité binaire** : SHA-256 réellement calculé sur les octets de chaque PDF, avec un booléen d'identité stricte. Un hash partagé n'est pas une preuve du producteur du fichier.
2. **Structure** : nombre réel de pages de chaque fichier; une différence n'est pas une preuve d'incohérence comptable.
3. **Correspondances textuelles** : extraction des textes par page, normalisation Unicode NFKC, harmonisation des espaces et calcul d'une empreinte SHA-256 **du texte normalisé**. Un appariement un-à-un d'une page municipale à une page ministérielle ne dépend pas du numéro de page. Une page sans texte extractible reste **indéterminée**, sans OCR et sans assertion d'absence.
4. **Ancrages P53W** : recherche des pages de couverture (index 0), du périmètre comptable (index 34) et de la section budgétaire (index 196), seulement si ces pages sont accessibles et leur texte extractible.

La copie locale du PDF doit résider **hors du dépôt GitHub**. Le programme refuse les chemins absolus d'entrée, la traversée de dossiers, les liens symboliques, les formats autres que PDF, les fichiers au-delà de 64 MiB, les PDFs chiffrés et ceux dépassant 1 200 pages. L'opérateur confirme qu'il peut consulter légalement les fichiers. Aucun document n'est contacté, obtenu, envoyé ou mis à jour automatiquement.

## Rapport partagé et détails privés

Le **bilan public** contient exclusivement des totaux/indicateurs agrégés, jamais de texte des pages, de chemin ou de hash de document. Le **détail privé facultatif** contient, lui, les SHA-256 et les indices de pages associés, pour relecture et conservation dans un espace autorisé, hors Git, avec permissions de fichier 0600.

Le traitement retourne une classe technique et des indicateurs comparatifs. Aucun accord sur les octets ou le texte ne certifie la version « officiellement autorisée » ; aucune discordance d'octets ou de texte ne prouve une irrégularité de gestion.

## Exécution

Installation de dépendance (pour le traitement local seulement) :

    python -m pip install pypdf==5.9.0

Inventaire neutre en l'absence d'originaux téléchargés localement :

    python scripts/comparer_versions_pdf_nova_p53x.py --bilan p53x_synthese.json

Comparaison hors Git, sur des copies licitement accessibles :

    python scripts/comparer_versions_pdf_nova_p53x.py --racine /repertoire-prive-documents --ville rapport_ville.pdf --mamh rapport_mamh.pdf --confirmer-acces-legal --bilan bilan_public.json --detail-prive /repertoire-prive/resultat_prive.json

Attestation impossible avec ce seul mécanisme :

    python scripts/comparer_versions_pdf_nova_p53x.py --exiger-certification

Code 0 : comparateur exécuté ou inventaire neutre; 2 : fichier/droit d'accès/format/racine non admissible; 3 : **refus attendu** de certifier les documents ou un montant. Les tests créent exclusivement des PDFs synthétiques. La CI ne télécharge, compare ou diffuse aucun PDF réel.

## Blocages économiques inchangés

La source 2024 n'authentifie pas les deux grands livres, contrats, paiements ou écritures d'élimination particulières. Les six questions bloquantes de P53W demeurent : version et provenance, comparabilité des publications, deux grands livres, éliminations déjà comptabilisées, protection des emplois et des services, avis juridiques/comptables originaux signés. Les deux scénarios constitutionnels restent séparés; les montants fiscaux Nova inconnus ne valent pas zéro.

**NO_GO_AUTOMATIQUE** : 0 économie certifiée, 0 avis indépendant signé, 0 rapprochement transactionnel attesté, 0 fusion ou suppression de services autorisée.
