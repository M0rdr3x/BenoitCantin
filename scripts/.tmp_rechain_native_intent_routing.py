from pathlib import Path

doc_path = Path('mobile-native/NATIVE_ROUTE_DISPATCH_V25.md')
doc = doc_path.read_text(encoding='utf-8')

old_alias_note = "Cette étape ne réécrit pas les liens profonds reçus par `Linking` ni les navigations internes déjà actives dans la WebView : ces chemins continuent de passer par `navigateToUrl` ou la navigation Web historique. Les sorties explicites des hubs avec `?surface=web` restent elles aussi des sorties Web volontaires."
new_alias_note = "Les intentions qui passent par `navigateToUrl` sont désormais résolues de façon cohérente : une route de `NATIVE_MODULE_PATHS` sans fragment et sans `surface=web` ouvre son sas natif, tandis qu’une sortie explicite `?surface=web` reste Web. Les navigations internes déjà actives dans la WebView ne sont pas interceptées par ce lot."
if old_alias_note not in doc:
    raise SystemExit('paragraphe historique des liens profonds introuvable')
doc = doc.replace(old_alias_note, new_alias_note, 1)

section_marker = "## Sortie explicite vers le Web\n"
intent_section = """## Routage des intentions du shell, liens profonds et notifications

`navigateToUrl` applique maintenant la classification avant d’ouvrir une WebView. Une URL interne vers une route de `NATIVE_MODULE_PATHS`, sans fragment et sans `surface=web`, converge vers `openNativeModule`. L’URL exacte `/compte/securite.html`, sans recherche ni fragment, ouvre le `NativeSecurityHub` dédié.

Les fragments Sécurité restent Web afin de préserver les vues précises des appareils, connexions, Mode Voyage, confirmations et préférences. Le Registre reste hors routeur et conserve son gate local ponctuel puis ses protections serveur.

`Linking.getInitialURL`, l’écouteur `Linking` et les réponses aux notifications passent déjà par `navigateToUrl` ou `navigate`; ils bénéficient donc de la même décision de surface. Le paramètre `surface=web` ne donne aucun droit : il choisit seulement la surface d’interface et ne remplace jamais authentification, RLS, AAL2, moteur de risque ou RPC.

Ce lot ne modifie pas `shouldStart` pour convertir les clics internes de la WebView en navigation native. Cette limite évite de casser un état Web contextuel déjà ouvert.

Le contrat complet est documenté dans `NATIVE_INTENT_ROUTING_V25.md` et verrouillé par `validate_mobile_native_intent_routing_v25.py`.

"""
if section_marker not in doc:
    raise SystemExit('section Sortie explicite vers le Web introuvable')
doc = doc.replace(section_marker, intent_section + section_marker, 1)

old_links = "Les liens profonds, notifications et autres navigations historiques restent gérés par `navigateToUrl`; cette étape n’intercepte pas arbitrairement des URLs externes ou des états Web précis."
new_links = "Les liens profonds et notifications restent gérés par `navigateToUrl`/`navigate`, mais les chemins classés natifs convergent maintenant vers leur sas avant toute WebView. Les URLs externes, les fragments Web et les pages volontairement exclues du routeur conservent leur comportement historique."
if old_links not in doc:
    raise SystemExit('paragraphe Sortie Web sur liens profonds introuvable')
doc = doc.replace(old_links, new_links, 1)

old_ci = "Le garde central exige la présence de chaque route primaire et de chaque composant actuellement routé. Son workflow revalide d’abord la **classification exhaustive des 42 pages du compte**, puis le garde des alias secondaires"
new_ci = "Le garde central exige la présence de chaque route primaire et de chaque composant actuellement routé. Son workflow revalide d’abord la **classification exhaustive des 42 pages du compte**, puis le **routage des intentions natives**, puis le garde des alias secondaires"
if old_ci not in doc:
    raise SystemExit('paragraphe CI central introuvable')
doc = doc.replace(old_ci, new_ci, 1)

doc_path.write_text(doc, encoding='utf-8')
