import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const destinations = [
  {
    label: 'Réseau personnage',
    description: 'Ouvrir la surface rôle-play protégée. Le fil, les profils de personnage et les interactions restent côté Web/serveur.',
    path: '/compte/reseau-personnage.html?surface=web',
  },
  {
    label: 'Communauté réelle',
    description: 'Ouvrir la communauté sans relier ici votre identité réelle à votre personnage.',
    path: '/compte/communaute.html?surface=web',
  },
  {
    label: 'Mon personnage',
    description: 'Gérer votre personnage dans sa surface dédiée sans copier ici fiche, portrait, statut ou identifiants.',
    path: '/compte/mon-personnage.html?surface=web',
  },
  {
    label: 'Sécurité et blocages',
    description: 'Utiliser les protections sociales existantes sans charger localement les personnes bloquées, signalements ou preuves.',
    path: '/compte/securite.html',
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

export function NativeCharacterNetworkHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Réseau personnage</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucune identité réelle, identité de personnage, publication, commentaire, réaction, relation sociale, groupe, blocage, signalement ni rôle propriétaire. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun graphe social dans le natif</Text>
        <Text style={styles.boundaryText}>
          Le sas ne charge ni abonnements, ni abonnés, ni groupes, ni membres, ni personnes consultées. Il ne construit aucun profil relationnel ou historique local de vos interactions.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>IDENTITÉS SÉPARÉES</Text>
        <Text style={styles.boundaryTitle}>Le compte réel reste distinct du personnage</Text>
        <Text style={styles.boundaryText}>
          Ce composant ne reçoit aucun courriel, nom réel, identifiant de compte, identifiant de personnage ou clé permettant de relier ces couches. La décision d’un rôle privilégié reste exclusivement côté serveur.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>RÔLE-PLAY ≠ CANON</Text>
        <Text style={styles.boundaryTitle}>Aucune décision narrative locale</Text>
        <Text style={styles.boundaryText}>
          Les publications et interactions du Réseau personnage ne sont jamais rendues canoniques par ce hub. Il ne décide ni canon, ni continuité, ni changement irréversible d’un personnage.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>MODÉRATION</Text>
        <Text style={styles.boundaryTitle}>Aucun signalement ou blocage reconstruit ici</Text>
        <Text style={styles.boundaryText}>
          Le hub ne publie, ne commente, ne réagit, ne suit, ne rejoint aucun groupe, ne bloque et ne signale personne. Les protections sociales restent dans leurs surfaces authentifiées.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les identités, contenus et décisions sociales restent dans les surfaces Web/serveur existantes. Le natif ne conserve aucun résumé du Réseau personnage.
      </Text>
      <View style={styles.destinationList}>
        {destinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Votre personnage n’est pas un moyen de révéler votre identité</Text>
        <Text style={styles.privacyText}>
          Le rôle-play peut créer des liens entre personnages sans exposer le compte réel sous-jacent. Ce sas conserve cette séparation et ne devient jamais une source de vérité sociale ou narrative.
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
