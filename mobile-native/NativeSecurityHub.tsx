import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  biometricEnabled: boolean;
  pushEnabled: boolean;
  onToggleBiometric: () => void;
  onTogglePush: () => void;
  onOpenPath: (path: string) => void;
  onClose: () => void;
};

const securityDestinations = [
  {
    label: 'Mes appareils',
    description: 'Voir les appareils connus, retirer une confiance ou déclarer un téléphone perdu.',
    path: '/compte/securite.html#devices-title',
  },
  {
    label: 'Connexions récentes',
    description: 'Consulter les connexions et les décisions explicables du bouclier de sécurité.',
    path: '/compte/securite.html#recent-title',
  },
  {
    label: 'Mode Voyage',
    description: 'Indiquer seulement une destination approximative et une période pour éviter les faux blocages.',
    path: '/compte/securite.html#travel-title',
  },
  {
    label: 'Connexions à confirmer',
    description: 'Autoriser ou refuser une tentative uniquement depuis un appareil fiable.',
    path: '/compte/securite.html#quick-title',
  },
  {
    label: 'Préférences de sécurité',
    description: 'Gérer les alertes et la protection renforcée des zones extrêmement sensibles.',
    path: '/compte/securite.html#preferences-title',
  },
] as const;

export function NativeSecurityHub({
  biometricEnabled,
  pushEnabled,
  onToggleBiometric,
  onTogglePush,
  onOpenPath,
  onClose,
}: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <View style={styles.headingRow}>
        <View style={styles.headingCopy}>
          <Text style={styles.eyebrow}>PROTÉGER SANS SURVEILLER</Text>
          <Text style={styles.title}>Ma sécurité</Text>
          <Text style={styles.intro}>
            Ce hub natif ne copie aucune donnée du compte. Les appareils, connexions, voyages et décisions restent dans le Centre de sécurité SINJIRA protégé par votre session.
          </Text>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="Fermer le hub sécurité natif" onPress={onClose} style={styles.closeButton}>
          <Text style={styles.closeText}>Fermer</Text>
        </Pressable>
      </View>

      <View style={styles.localGrid}>
        <View style={styles.localCard}>
          <Text style={styles.cardKicker}>Sur ce téléphone</Text>
          <Text style={styles.cardTitle}>Protection biométrique</Text>
          <Text style={styles.cardText}>
            {biometricEnabled
              ? 'Active. La biométrie reste gérée par iOS ou Android et ne quitte pas l’appareil.'
              : 'Inactive. Vous pouvez l’activer volontairement si une biométrie est configurée sur le téléphone.'}
          </Text>
          <Pressable accessibilityRole="button" onPress={onToggleBiometric} style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>{biometricEnabled ? 'Désactiver localement' : 'Activer localement'}</Text>
          </Pressable>
        </View>

        <View style={styles.localCard}>
          <Text style={styles.cardKicker}>Alertes discrètes</Text>
          <Text style={styles.cardTitle}>Notifications de sécurité</Text>
          <Text style={styles.cardText}>
            {pushEnabled
              ? 'Actives. Les alertes restent génériques sur l’écran verrouillé.'
              : 'Inactives. SINJIRA continue de protéger le compte même sans notification push.'}
          </Text>
          <Pressable accessibilityRole="button" onPress={onTogglePush} style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>{pushEnabled ? 'Désactiver les alertes' : 'Activer les alertes'}</Text>
          </Pressable>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Centre de sécurité</Text>
      <Text style={styles.sectionText}>
        Les opérations ci-dessous ouvrent la surface Web existante afin de conserver une seule source de vérité et les mêmes contrôles AAL2/RPC sur Web et mobile.
      </Text>

      <View style={styles.destinationList}>
        {securityDestinations.map((item) => (
          <Pressable
            key={item.path}
            accessibilityRole="button"
            accessibilityLabel={`Ouvrir ${item.label}`}
            onPress={() => onOpenPath(item.path)}
            style={styles.destinationCard}
          >
            <View style={styles.destinationCopy}>
              <Text style={styles.destinationTitle}>{item.label}</Text>
              <Text style={styles.destinationText}>{item.description}</Text>
            </View>
            <Text style={styles.chevron} accessible={false}>›</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Vie privée</Text>
        <Text style={styles.privacyText}>
          Ce hub ne demande aucun GPS, n’affiche aucune adresse IP, ne stocke aucune confidence et ne reçoit ni visage ni empreinte. Les protections locales servent uniquement à défendre votre compte.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#070914' },
  content: { padding: 16, paddingBottom: 28, gap: 16 },
  headingRow: { gap: 12 },
  headingCopy: { gap: 6 },
  eyebrow: { color: '#9ca8ca', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  title: { color: '#ffffff', fontSize: 28, fontWeight: '900' },
  intro: { color: '#bec7e4', fontSize: 14, lineHeight: 20 },
  closeButton: { alignSelf: 'flex-start', borderWidth: 1, borderColor: '#384260', borderRadius: 999, paddingHorizontal: 13, paddingVertical: 8 },
  closeText: { color: '#eef1ff', fontWeight: '800', fontSize: 12 },
  localGrid: { gap: 10 },
  localCard: { borderWidth: 1, borderColor: '#26304d', borderRadius: 16, backgroundColor: '#10162a', padding: 14, gap: 8 },
  cardKicker: { color: '#91a0c7', fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.9 },
  cardTitle: { color: '#ffffff', fontSize: 17, fontWeight: '800' },
  cardText: { color: '#b8c2df', fontSize: 13, lineHeight: 19 },
  primaryButton: { alignSelf: 'flex-start', borderRadius: 10, backgroundColor: '#e4e9ff', paddingHorizontal: 13, paddingVertical: 9 },
  primaryButtonText: { color: '#10152a', fontWeight: '800', fontSize: 12 },
  sectionTitle: { color: '#ffffff', fontSize: 19, fontWeight: '900', marginTop: 4 },
  sectionText: { color: '#aeb9d8', fontSize: 13, lineHeight: 19, marginTop: -10 },
  destinationList: { gap: 9 },
  destinationCard: { flexDirection: 'row', alignItems: 'center', gap: 12, borderWidth: 1, borderColor: '#252d45', backgroundColor: '#0e1427', borderRadius: 14, padding: 14 },
  destinationCopy: { flex: 1, gap: 4 },
  destinationTitle: { color: '#ffffff', fontSize: 15, fontWeight: '800' },
  destinationText: { color: '#aeb9d8', fontSize: 12, lineHeight: 18 },
  chevron: { color: '#dce3ff', fontSize: 28, fontWeight: '300' },
  privacyNote: { borderRadius: 14, borderWidth: 1, borderColor: '#27314d', backgroundColor: '#0b1020', padding: 14, gap: 5 },
  privacyTitle: { color: '#eef1ff', fontSize: 14, fontWeight: '800' },
  privacyText: { color: '#aeb9d8', fontSize: 12, lineHeight: 18 },
});
