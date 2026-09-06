import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativePrivacyHub } from './NativePrivacyHub';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const profileDestinations = [
  {
    label: 'Modifier mon profil',
    description: 'Ouvrir le profil complet existant pour le nom affiché, la photo et les informations personnelles protégées.',
    path: '/compte/profil.html?surface=web',
  },
  {
    label: 'Vie privée',
    description: 'Ouvrir un hub natif sans données avant le Centre Vie privée existant.',
    path: '/compte/vie-privee.html',
  },
  {
    label: 'Paramètres',
    description: 'Gérer les préférences, l’export des données et les actions de compte dans la surface Web protégée.',
    path: '/compte/parametres.html',
  },
  {
    label: 'Ma sécurité',
    description: 'Ouvrir le Centre de sécurité existant pour les opérations qui restent contrôlées côté serveur.',
    path: '/compte/securite.html',
  },
] as const;

function DestinationCard({
  label,
  description,
  onPress,
}: {
  label: string;
  description: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Ouvrir ${label}`}
      onPress={onPress}
      style={styles.destinationCard}
    >
      <View style={styles.destinationCopy}>
        <Text style={styles.destinationTitle}>{label}</Text>
        <Text style={styles.destinationText}>{description}</Text>
      </View>
      <Text style={styles.chevron} accessible={false}>›</Text>
    </Pressable>
  );
}

export function NativeProfileHub({ onOpenPath, onBack }: Props) {
  const [privacyHubOpen, setPrivacyHubOpen] = useState(false);

  if (privacyHubOpen) {
    return (
      <NativePrivacyHub
        onBack={() => setPrivacyHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  const openProfileDestination = (path: string) => {
    if (path === '/compte/vie-privee.html') {
      setPrivacyHubOpen(true);
      return;
    }
    onOpenPath(path);
  };

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Retour à l’accueil"
        onPress={onBack}
        style={styles.backButton}
      >
        <Text style={styles.backButtonText}>‹ Accueil</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Profil</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit, ne copie et ne conserve aucune donnée de profil. Il sert uniquement à vous orienter vers les surfaces SINJIRA qui restent la source de vérité.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Vos renseignements restent où ils sont protégés</Text>
        <Text style={styles.boundaryText}>
          Le nom affiché, le courriel, la photo, la date de naissance, la résidence, les relations et les préférences ne sont pas chargés dans cet écran. Les formulaires Web existants conservent leurs règles RLS, d’admissibilité et de sécurité.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Profil et contrôles</Text>
      <Text style={styles.sectionText}>
        Choisissez une destination. Le natif n’effectue aucune modification de compte lui-même.
      </Text>
      <View style={styles.destinationList}>
        {profileDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => openProfileDestination(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Aucune seconde copie du profil</Text>
        <Text style={styles.privacyText}>
          Cette frontière native ne possède ni stockage local de profil, ni appel Supabase, ni RPC, ni logique d’export ou de suppression. Les actions sensibles restent dans leurs modules existants.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#070914' },
  content: { padding: 16, paddingBottom: 28, gap: 16 },
  backButton: { alignSelf: 'flex-start', minHeight: 40, justifyContent: 'center', paddingHorizontal: 4 },
  backButtonText: { color: '#dce3ff', fontSize: 14, fontWeight: '800' },
  hero: { gap: 7 },
  eyebrow: { color: '#9ca8ca', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  title: { color: '#ffffff', fontSize: 30, fontWeight: '900' },
  intro: { color: '#bec7e4', fontSize: 14, lineHeight: 20 },
  boundaryCard: { borderWidth: 1, borderColor: '#384260', borderRadius: 18, backgroundColor: '#10162a', padding: 15, gap: 6 },
  cardKicker: { color: '#91a0c7', fontSize: 10, fontWeight: '800', letterSpacing: 0.9 },
  boundaryTitle: { color: '#ffffff', fontSize: 17, fontWeight: '900' },
  boundaryText: { color: '#b8c2df', fontSize: 13, lineHeight: 19 },
  sectionTitle: { color: '#ffffff', fontSize: 19, fontWeight: '900', marginTop: 2 },
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
