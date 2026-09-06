import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeMessagesHub } from './NativeMessagesHub';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const alertDestinations = [
  {
    label: 'Voir mes avis privés',
    description: 'Ouvrir la liste complète existante avec son état lu/non lu dans la surface Web protégée.',
    path: '/compte/notifications.html?surface=web',
  },
  {
    label: 'Ma sécurité',
    description: 'Accéder au Centre de sécurité pour les alertes et événements qui concernent la protection du compte.',
    path: '/compte/securite.html',
  },
  {
    label: 'Messages',
    description: 'Ouvrir le hub natif sans contenu privé avant de choisir votre identité de messagerie.',
    path: '/compte/messages.html',
  },
  {
    label: 'Préférences',
    description: 'Gérer les préférences internes de notification dans la surface Paramètres protégée.',
    path: '/compte/parametres.html?surface=web',
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

export function NativeAlertsHub({ onOpenPath, onBack }: Props) {
  const [messagesHubOpen, setMessagesHubOpen] = useState(false);

  if (messagesHubOpen) {
    return (
      <NativeMessagesHub
        onBack={() => setMessagesHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  const openDestination = (path: string) => {
    if (path === '/compte/messages.html') {
      setMessagesHubOpen(true);
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
        <Text style={styles.title}>Alertes</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucune notification privée, aucun compteur et aucun état lu/non lu. Il sert uniquement à vous orienter vers les modules SINJIRA existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun contenu d’avis n’est copié dans le natif</Text>
        <Text style={styles.boundaryText}>
          Les avis de compte, leurs catégories, leurs liens, leurs compteurs et l’action de marquage lu/non lu restent dans la surface Web et ses règles RLS. Ce composant n’a aucune source de vérité propre.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Le natif ne marque, ne crée et ne supprime aucun avis.
      </Text>
      <View style={styles.destinationList}>
        {alertDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => openDestination(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Pas de résumé local de votre activité</Text>
        <Text style={styles.privacyText}>
          Aucun nombre d’avis, aperçu, date, expéditeur, événement de sécurité ou activité communautaire n’est conservé dans cet écran React Native.
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
