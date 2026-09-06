import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const messageDestinations = [
  {
    label: 'Choisir mon identité',
    description: 'Ouvrir le sélecteur Web existant sans mémoriser localement si vous utilisez votre compte réel ou votre personnage.',
    path: '/compte/messages.html?surface=web',
  },
  {
    label: 'Compte réel',
    description: 'Accéder à la messagerie de communauté avec le pseudo et l’avatar de compte dans sa surface privée existante.',
    path: '/compte/messages-reels.html?surface=web',
  },
  {
    label: 'Personnage',
    description: 'Accéder séparément à la messagerie de rôle-play sous l’identité du personnage SINJIRA™.',
    path: '/compte/messages-personnage.html?surface=web',
  },
  {
    label: 'Comptes bloqués',
    description: 'Gérer vos blocages dans la surface de sécurité sociale existante.',
    path: '/compte/blocages.html',
  },
  {
    label: 'Règles de la communauté',
    description: 'Relire les règles applicables aux échanges avant ou pendant une conversation.',
    path: '/compte/regles-communaute.html',
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

export function NativeMessagesHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Retour"
        onPress={onBack}
        style={styles.backButton}
      >
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Messages</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun message privé, aucune conversation, aucun participant, aucun compteur non lu et aucun état lu/non lu. Il sert uniquement à choisir explicitement la bonne surface SINJIRA.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Votre identité reste un choix explicite</Text>
        <Text style={styles.boundaryText}>
          SINJIRA sépare la messagerie du compte réel et celle du personnage. Le natif ne choisit jamais votre identité à votre place, ne fusionne pas ces deux contextes et ne mémorise pas votre dernier choix.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Le natif n’envoie, ne modifie, ne supprime et ne marque aucun message.
      </Text>
      <View style={styles.destinationList}>
        {messageDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Aucun aperçu de conversation n’est copié dans le natif</Text>
        <Text style={styles.privacyText}>
          Aucun texte, nom de participant, avatar, date, statut, compteur ou extrait de conversation n’est conservé par cet écran React Native. La source de vérité reste la messagerie Web protégée et ses règles d’accès.
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
