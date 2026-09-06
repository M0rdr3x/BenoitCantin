import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeSettingsHub } from './NativeSettingsHub';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const privacyDestinations = [
  {
    label: 'Exercer mes droits',
    description: 'Ouvrir le formulaire Vie privée existant pour une demande d’accès, rectification, portabilité, suppression ou autre droit applicable.',
    path: '/compte/vie-privee.html?surface=web',
  },
  {
    label: 'Politique générale',
    description: 'Consulter la politique de confidentialité publique de SINJIRA.',
    path: '/confidentialite.html',
  },
  {
    label: 'Ma sécurité',
    description: 'Pour un enjeu de sécurité ou de protection, ouvrir le Centre de sécurité existant.',
    path: '/compte/securite.html',
  },
  {
    label: 'Paramètres du compte',
    description: 'Ouvrir un hub natif sans préférences locales avant les actions protégées du compte.',
    path: '/compte/parametres.html',
  },
] as const;

function DestinationCard({ label, description, onPress }: { label: string; description: string; onPress: () => void }) {
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

export function NativePrivacyHub({ onOpenPath, onBack }: Props) {
  const [settingsHubOpen, setSettingsHubOpen] = useState(false);

  if (settingsHubOpen) {
    return (
      <NativeSettingsHub
        onBack={() => setSettingsHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  const openPrivacyDestination = (path: string) => {
    if (path === '/compte/parametres.html') {
      setSettingsHubOpen(true);
      return;
    }
    onOpenPath(path);
  };

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Retour au profil"
        onPress={onBack}
        style={styles.backButton}
      >
        <Text style={styles.backButtonText}>‹ Profil</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Vie privée</Text>
        <Text style={styles.intro}>
          Ce hub natif explique la frontière et vous oriente. Il ne lit aucune demande Vie privée, aucun renseignement personnel et aucun historique de votre compte.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>VOS DROITS RESTENT SOUS VOTRE CONTRÔLE</Text>
        <Text style={styles.boundaryTitle}>Aucune demande n’est traitée localement</Text>
        <Text style={styles.boundaryText}>
          Les demandes, leur état et toute vérification d’identité restent dans le Centre Vie privée Web et ses contrôles serveur. Le natif ne crée, ne modifie et ne conserve aucun dossier de vie privée.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les actions réelles continuent dans les surfaces canoniques existantes.
      </Text>
      <View style={styles.destinationList}>
        {privacyDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => openPrivacyDestination(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Protéger sans surveiller</Text>
        <Text style={styles.privacyText}>
          Aucun GPS, aucune adresse IP brute, aucun secret, aucune pièce d’identité et aucun contenu d’une demande ne sont demandés par cet écran natif.
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
