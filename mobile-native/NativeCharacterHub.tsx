import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const characterDestinations = [
  {
    label: 'Ouvrir Mon personnage',
    description: 'Continuer dans la surface Web privée qui affiche uniquement la fiche narrative autorisée pour votre compte.',
    path: '/compte/mon-personnage.html?surface=web',
  },
  {
    label: 'Monde parallèle',
    description: 'Ouvrir la continuité existante sans copier ici votre identité de personnage ni votre Chronique privée.',
    path: '/compte/monde-parallele.html?surface=web',
  },
  {
    label: 'Ma sécurité',
    description: 'Consulter les protections du compte sans exposer les liens techniques entre compte et personnage.',
    path: '/compte/securite.html',
  },
  {
    label: 'Vie privée',
    description: 'Consulter les règles de confidentialité sans charger la fiche humaine source dans le natif.',
    path: '/compte/vie-privee.html?surface=web',
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

export function NativeCharacterHub({ onOpenPath, onBack }: Props) {
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
        <Text style={styles.title}>Mon personnage</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun nom public, portrait, description, bible narrative, psychologie, statut, canon, roman, soumission ni fiche humaine source. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>La fiche humaine source reste privée</Text>
        <Text style={styles.boundaryText}>
          Le Registre peut servir de source au processus de création du personnage, mais le questionnaire humain et ses réponses privées ne sont pas copiés dans ce hub. La surface personnage n’affiche que la matière narrative validée selon les règles existantes.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>DÉCISION HUMAINE</Text>
        <Text style={styles.boundaryTitle}>Le natif ne transforme personne en personnage</Text>
        <Text style={styles.boundaryText}>
          Ce hub ne crée, n’approuve, ne refuse, n’archive et n’attribue aucun personnage à un roman. Il ne décide jamais du canon, de la psychologie narrative ou de la visibilité d’une fiche.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>UNE SEULE SOURCE DE VÉRITÉ</Text>
        <Text style={styles.boundaryTitle}>Aucune réparation ou synchronisation locale</Text>
        <Text style={styles.boundaryText}>
          Le natif n’appelle aucune réparation propriétaire, ne charge aucune soumission et ne synchronise aucune fiche personnage. Les vérifications authentifiées et la persistance restent dans les mécanismes Web et serveur existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>IDENTITÉS CLOISONNÉES</Text>
        <Text style={styles.boundaryTitle}>Compte, personnage et continuité restent distincts</Text>
        <Text style={styles.boundaryText}>
          Le profil humain du compte, le nom public du personnage et les identifiants techniques privés ne sont pas fusionnés dans le natif. Ce hub ne reçoit aucune clé interne permettant de relier ces couches.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les données et décisions restent dans leurs surfaces existantes. Le natif ne conserve aucun résumé local de votre personnage.
      </Text>
      <View style={styles.destinationList}>
        {characterDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Votre personne n’est pas votre fiche narrative</Text>
        <Text style={styles.privacyText}>
          SINJIRA doit préserver la séparation entre la personne réelle et sa représentation narrative. Ce sas n’extrait aucune donnée humaine du Registre et ne devient jamais la source de vérité du personnage.
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
