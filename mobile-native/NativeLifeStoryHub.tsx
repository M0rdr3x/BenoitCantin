import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const lifeStoryDestinations = [
  {
    label: 'Ouvrir Histoire de vie',
    description: 'Continuer dans la surface Web privée qui applique AAL2 avant les souvenirs, versions, destinataires et directives.',
    path: '/compte/histoire-de-vie.html?surface=web',
  },
  {
    label: 'Ma sécurité',
    description: 'Vérifier les protections du compte avant d’ouvrir une surface contenant des choix personnels ou posthumes.',
    path: '/compte/securite.html',
  },
  {
    label: 'Vie privée',
    description: 'Consulter les règles de confidentialité sans copier ici vos choix Histoire de vie.',
    path: '/compte/vie-privee.html?surface=web',
  },
  {
    label: 'Mon IA',
    description: 'Gérer Mon IA séparément. Ouvrir ce lien n’autorise jamais Histoire de vie comme source.',
    path: '/compte/mon-ia.html?surface=web',
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

export function NativeLifeStoryHub({ onOpenPath, onBack }: Props) {
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
        <Text style={styles.title}>Histoire de vie</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun souvenir, récit, titre, date, version, destinataire, courriel, directive, dossier posthume, code privé ou aperçu. Il sert uniquement à vous orienter vers la surface privée existante.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Enregistrer n’est jamais transmettre</Text>
        <Text style={styles.boundaryText}>
          Le natif ne crée, ne modifie, n’autorise, ne classe et ne supprime aucun élément Histoire de vie. Enregistrer un souvenir, l’autoriser pour une œuvre et choisir une version restent trois décisions distinctes dans la surface privée.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>FRONTIÈRE POSTHUME</Text>
        <Text style={styles.boundaryTitle}>Aucune remise automatique</Text>
        <Text style={styles.boundaryText}>
          Le hub ne signale ni ne valide un décès, ne choisit aucun destinataire et ne prépare aucun PDF. La procédure existante exige un décès vérifié humainement, un délai de sécurité de 30 jours sans contestation et une deuxième validation humaine avant toute préparation.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CONTESTATION TOUJOURS PRIORITAIRE</Text>
        <Text style={styles.boundaryTitle}>Une déclaration incorrecte doit pouvoir tout suspendre</Text>
        <Text style={styles.boundaryText}>
          Ce composant ne lit aucun état de procédure et n’enregistre aucune contestation. La contestation d’une vérification de décès reste une opération privée côté Web/serveur qui suspend la suite du processus jusqu’à révision humaine.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CODES ET PROCHES</Text>
        <Text style={styles.boundaryTitle}>Aucun code privé ni coordonnée n’est géré nativement</Text>
        <Text style={styles.boundaryText}>
          Le hub ne crée, n’affiche, ne copie ni ne révoque de code privé de signalement de décès. Il ne lit ni ne stocke le nom, la description ou le courriel d’un proche.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>REGISTRE SÉPARÉ</Text>
        <Text style={styles.boundaryTitle}>Le Registre personnel n’entre jamais dans Histoire de vie automatiquement</Text>
        <Text style={styles.boundaryText}>
          Aucun contenu du Registre personnel des consciences n’est copié dans ce hub, dans une œuvre ou dans une remise posthume. Histoire de vie utilise seulement les éléments que la personne choisit d’y enregistrer et d’y autoriser séparément.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>AUCUN CLONE IA</Text>
        <Text style={styles.boundaryTitle}>Une histoire numérique ne devient pas une personne simulée</Text>
        <Text style={styles.boundaryText}>
          Ce hub ne crée aucun clone IA, n’expose aucune mémoire à un proche et ne transforme jamais une reconstruction en fait connu. Mon IA reste une fonction privée et séparée.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les données, consentements et protections restent dans leurs surfaces actuelles. Le natif ne conserve aucun résumé local de votre Histoire de vie.
      </Text>
      <View style={styles.destinationList}>
        {lifeStoryDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Vos choix restent vos choix</Text>
        <Text style={styles.privacyText}>
          SINJIRA ne choisit pas vos souvenirs, vos destinataires ni ce qui doit être transmis. Le rôle de cette surface native est seulement d’expliquer la frontière avant l’ouverture de la zone privée.
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
