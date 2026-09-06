import { NativeAlertsHub } from './NativeAlertsHub';
import { NativeDatingHub } from './NativeDatingHub';
import { NativeEmploymentHub } from './NativeEmploymentHub';
import { NativeLifeStoryHub } from './NativeLifeStoryHub';
import { NativeMessagesHub } from './NativeMessagesHub';
import { NativeParallelWorldHub } from './NativeParallelWorldHub';
import { NativePersonalAiHub } from './NativePersonalAiHub';
import { NativeProfileHub } from './NativeProfileHub';

export const NATIVE_MODULE_PATHS = [
  '/compte/messages.html',
  '/compte/rencontres.html',
  '/compte/emploi.html',
  '/compte/monde-parallele.html',
  '/compte/mon-ia.html',
  '/compte/histoire-de-vie.html',
  '/compte/notifications.html',
  '/compte/profil.html',
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
      return <NativeMessagesHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/rencontres.html':
      return <NativeDatingHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/emploi.html':
      return <NativeEmploymentHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/monde-parallele.html':
      return <NativeParallelWorldHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/mon-ia.html':
      return <NativePersonalAiHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/histoire-de-vie.html':
      return <NativeLifeStoryHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/notifications.html':
      return <NativeAlertsHub onOpenPath={onOpenPath} onBack={onBack} />;
    case '/compte/profil.html':
      return <NativeProfileHub onOpenPath={onOpenPath} onBack={onBack} />;
    default:
      return null;
  }
}
