import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const parallelWorldDestinations = [
  {
    label: 'Mon espace parallèle',
    description: 'Ouvrir la surface Web privée qui gère votre continuité, votre cycle et votre Chronique personnelle.',
    path: '/compte/monde-parallele.html?surface=web',
  },
  {
    label: 'Portail public',
    description: 'Consulter la présentation publique du Monde parallèle sans charger votre état privé dans le natif.',
    path: '/projets/sinjira/monde-parallele/',
  },
  {
    label: 'Mon personnage',
    description: 'Ouvrir la surface personnage existante. Les identités de compte et de personnage restent séparées.',
    path: '/compte/mon-personnage.html',
  },
  {
    label: 'Ma sécurité',
    description: 'Ouvrir le Centre de sécurité sans exposer les clés techniques qui relient le compte à la continuité.',
    path: '/compte/securite.html',
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

export function NativeParallelWorldHub({ onOpenPath, onBack }: Props) {
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
        <Text style={styles.title}>Monde parallèle</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucune identité de personnage, adhésion, réputation, localisation narrative, faction, Chronique personnelle, réponse de cycle ni histoire liée à votre continuité. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Les identités restent cloisonnées</Text>
        <Text style={styles.boundaryText}>
          Le nom public du personnage, le profil du compte et l’identifiant technique privé restent des couches séparées. Le natif ne reçoit aucune clé interne permettant de relier ces identités.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CONTINUITÉ CÔTÉ SERVEUR</Text>
        <Text style={styles.boundaryTitle}>Aucune mémoire narrative locale</Text>
        <Text style={styles.boundaryText}>
          Réputation, lieu, faction, résumé narratif privé, numéro de pionnier, état de vie et historique personnel restent dans les mécanismes Web et serveur existants. Cet écran n’en conserve aucun résumé.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Le natif ne crée, ne modifie et n’enregistre aucune réponse de cycle, aucun état narratif et aucune histoire.
      </Text>
      <View style={styles.destinationList}>
        {parallelWorldDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Le canon reste une décision humaine</Text>
        <Text style={styles.privacyText}>
          Ce hub ne valide aucun canon, décès, mémorial ou changement irréversible du personnage. Il ne prend aucune décision narrative et ne devient jamais la source de vérité de votre continuité.
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
