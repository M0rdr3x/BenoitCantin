import { NativeAlertsHub } from './NativeAlertsHub';
import { NativeCharacterHub } from './NativeCharacterHub';
import { NativeCharacterNetworkHub } from './NativeCharacterNetworkHub';
import { NativeCommerceHub } from './NativeCommerceHub';
import { NativeCommunityHub } from './NativeCommunityHub';
import { NativeDatingHub } from './NativeDatingHub';
import { NativeEmploymentHub } from './NativeEmploymentHub';
import { NativeGamesHub } from './NativeGamesHub';
import { NativeLibraryHub } from './NativeLibraryHub';
import { NativeLifeStoryHub } from './NativeLifeStoryHub';
import { NativeMessagesHub } from './NativeMessagesHub';
import { NativeParallelWorldHub } from './NativeParallelWorldHub';
import { NativePersonalAiHub } from './NativePersonalAiHub';
import { NativePrivacyHub } from './NativePrivacyHub';
import { NativeProfileHub } from './NativeProfileHub';
import { NativeRelationsHub } from './NativeRelationsHub';
import { NativeSettingsHub } from './NativeSettingsHub';

export const NATIVE_MODULE_PATHS = [
  '/compte/messages.html',
  '/compte/messages-reels.html',
  '/compte/messages-personnage.html',
  '/compte/rencontres.html',
  '/compte/emploi.html',
  '/compte/bibliotheque.html',
  '/compte/mes-lectures.html',
  '/compte/documents.html',
  '/compte/playtests.html',
  '/compte/mes-parties.html',
  '/compte/contributions.html',
  '/compte/communaute.html',
  '/compte/mes-commentaires.html',
  '/compte/blocages.html',
  '/compte/regles-communaute.html',
  '/compte/moderation.html',
  '/compte/reseau-personnage.html',
  '/compte/relations.html',
  '/compte/mes-achats.html',
  '/compte/marche.html',
  '/compte/jetons.html',
  '/compte/licences.html',
  '/compte/monde-parallele.html',
  '/compte/mon-ia.html',
  '/compte/histoire-de-vie.html',
  '/compte/mon-personnage.html',
  '/compte/mes-personnages.html',
  '/compte/notifications.html',
  '/compte/profil.html',
  '/compte/vie-privee.html',
  '/compte/parametres.html',
] as const;

export type NativeModulePath = (typeof NATIVE_MODULE_PATHS)[number];

type Props = {
  path: NativeModulePath;
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

export function isNativeModulePath(path: string): path is NativeModulePath {
  return (NATIVE_MODULE_PATHS as readonly string[]).includes(path);
}

export function NativeModuleRouter({ path, onOpenPath, onBack }: Props) {
  switch (path) {
    case '/compte/messages.html':
    case '/compte/messages-reels.html':
    case '/compte/messages-personnage.html':
      return <NativeMessagesHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/rencontres.html':
      return <NativeDatingHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/emploi.html':
      return <NativeEmploymentHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/bibliotheque.html':
    case '/compte/mes-lectures.html':
    case '/compte/documents.html':
    case '/compte/playtests.html':
      return <NativeLibraryHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/mes-parties.html':
    case '/compte/contributions.html':
      return <NativeGamesHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/communaute.html':
    case '/compte/mes-commentaires.html':
    case '/compte/blocages.html':
    case '/compte/regles-communaute.html':
    case '/compte/moderation.html':
      return <NativeCommunityHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/reseau-personnage.html':
      return <NativeCharacterNetworkHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/relations.html':
      return <NativeRelationsHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/mes-achats.html':
    case '/compte/marche.html':
    case '/compte/jetons.html':
    case '/compte/licences.html':
      return <NativeCommerceHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/monde-parallele.html':
      return <NativeParallelWorldHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/mon-ia.html':
      return <NativePersonalAiHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/histoire-de-vie.html':
      return <NativeLifeStoryHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/mon-personnage.html':
    case '/compte/mes-personnages.html':
      return <NativeCharacterHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/notifications.html':
      return <NativeAlertsHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/profil.html':
      return <NativeProfileHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/vie-privee.html':
      return <NativePrivacyHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/parametres.html':
      return <NativeSettingsHub onOpenPath={onOpenPath} onBack={onBack} />;
    default:
      return null;
  }
}
