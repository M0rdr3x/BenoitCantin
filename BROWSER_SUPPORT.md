# Compatibilité navigateur — SINJIRA V24.4.22

Le portail suit une stratégie de **progressive enhancement** : le contenu public, la navigation, les formulaires et les liens essentiels doivent rester utilisables même lorsqu’un moteur ignore une fonction CSS récente.

## Moteurs testés automatiquement

Chaque modification est testée avec Playwright sur les trois familles de moteurs qui couvrent les navigateurs majeurs :

- **Chromium** — Chrome, Edge, Opera, Brave et navigateurs Chromium modernes;
- **Firefox** — Firefox desktop et moteur Gecko;
- **WebKit** — Safari macOS/iOS et navigateurs iOS basés sur WebKit.

Les tests vérifient un profil desktop et un profil mobile étroit, l’ouverture/fermeture du menu, les routes publiques critiques, l’absence de débordement horizontal, la couche de compatibilité CSS et le runtime public.

## Politique de support

Le support garanti vise les versions stables actuelles et récentes de Chrome/Edge/Firefox/Safari ainsi que Safari iOS et les navigateurs Android modernes. Les anciens navigateurs sans modules JavaScript bénéficient d’un portail public dégradé proprement : le contenu reste lisible et la navigation principale utilise un noyau JavaScript sans syntaxe moderne obligatoire.

Les fonctions privées complexes — authentification, temps réel, administration, jeux en ligne et APIs sécurisées — nécessitent un navigateur moderne avec ES Modules, Fetch, Web Crypto et les primitives de sécurité web actuelles.

Internet Explorer n’est pas une cible de sécurité ou de fonctionnalité complète. Il est obsolète et ne reçoit plus les standards de sécurité nécessaires aux fonctions privées modernes.

## Fallbacks inclus

La couche `assets/css/browser-compat-v24-4-22.css` fournit notamment les variantes WebKit nécessaires, les fallbacks de largeur et de typographie, le contraste sans `backdrop-filter`, les zones sûres iOS, la prévention du zoom involontaire des champs mobiles et la réduction des animations.
