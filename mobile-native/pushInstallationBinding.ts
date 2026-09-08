export type PushInstallationBindingInput = {
  optedIn: boolean;
  token: string;
  boundDeviceKey: string;
  currentDeviceKey: string;
};

export function reusablePushTokenForInstallation({
  optedIn,
  token,
  boundDeviceKey,
  currentDeviceKey,
}: PushInstallationBindingInput) {
  if (!optedIn || !token || !boundDeviceKey || !currentDeviceKey) return '';
  return boundDeviceKey === currentDeviceKey ? token : '';
}
