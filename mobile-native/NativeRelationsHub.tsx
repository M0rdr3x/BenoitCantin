import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const relationsDestinations = [
  {
    label: 'Relations et famille',
    description: 'Ouvrir la surface privée existante. Les relations, notes et liens de supervision restent côté Web/serveur.',
    path: '/compte/relations.html?surface=web',
  },
  {
    label: 'Ma sécurité',
    description: 'Consulter les protections du compte sans copier ici la tranche d’âge, les liens de supervision ou les métadonnées de contact.',
    path: '/compte/securite.html',
  },
  {
    label: 'Vie privée',
    description: 'Consulter les règles de confidentialité et les contrôles de données dans leur surface officielle.',
    path: '/compte/vie-privee.html',
  },
] as const;

function DestinationCard({ label, description, onPress }: { label: string; description: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={`Ouvrir ${label}`} onPress={onPress} style={styles.destinationCard}>
      <View style={styles.destinationCopy}>
        <Text style={styles.destinationTitle}>{label}</Text>
        <Text style={styles.destinationText}>{description}</Text>
      </View>
      <Text style={styles.chevron} accessible={false}>›</Text>
    </Pressable>
  );
}

export function NativeRelationsHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Relations et famille</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucune relation familiale, note privée, tranche d’âge, autorisation parentale, code à usage unique, lien de supervision ou métadonnée de contact. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun graphe familial local</Text>
        <Text style={styles.boundaryText}>
          Le natif ne reçoit ni noms, ni pseudos, ni types de relation, ni dates, ni notes privées. Il ne reconstruit pas votre famille ou vos relations pour créer un profil de votre entourage.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>SUPERVISION JEUNESSE</Text>
        <Text style={styles.boundaryTitle}>Le serveur décide des outils disponibles</Text>
        <Text style={styles.boundaryText}>
          Ce sas ne connaît pas votre tranche d’âge et ne choisit jamais si les outils adulte, jeunesse ou neutres doivent apparaître. Cette décision reste fondée sur l’état serveur du compte.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CODES PARENTAUX</Text>
        <Text style={styles.boundaryTitle}>Aucun code n’est créé, lu ou mémorisé ici</Text>
        <Text style={styles.boundaryText}>
          Les codes d’autorisation parentale à usage unique restent dans la surface authentifiée. Le natif ne peut ni générer, ni saisir, ni valider, ni afficher un code, et ne conserve jamais sa valeur.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>LIENS DE SUPERVISION</Text>
        <Text style={styles.boundaryTitle}>Aucune relation tuteur–mineur n’est copiée</Text>
        <Text style={styles.boundaryText}>
          Le hub ne lit ni statut de supervision, ni rôle du tuteur, ni métadonnée de contact autorisée. Il ne révoque pas un lien et n’accède jamais au contenu privé des messages.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les relations privées et la supervision restent dans leurs mécanismes existants. Le natif ne conserve aucun résumé de votre entourage.
      </Text>
      <View style={styles.destinationList}>
        {relationsDestinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>La supervision protège sans ouvrir les messages</Text>
        <Text style={styles.privacyText}>
          Un lien de supervision peut autoriser certaines métadonnées prévues par le système, mais il ne donne pas accès au contenu privé des messages. Ce sas n’élargit jamais cette frontière.
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
