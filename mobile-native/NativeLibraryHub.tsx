import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const libraryDestinations = [
  {
    label: 'Ouvrir Ma bibliothèque',
    description: 'Continuer dans la surface Web privée qui applique les droits réels de votre compte.',
    path: '/compte/bibliotheque.html?surface=web',
  },
  {
    label: 'Mes lectures',
    description: 'Consulter vos lectures et leur progression dans la surface Web protégée, sans progression copiée dans le natif.',
    path: '/compte/mes-lectures.html?surface=web',
  },
  {
    label: 'Mes playtests',
    description: 'Consulter candidatures, invitations et participations dans la surface Web, sans admissibilité ni historique testeur copié localement.',
    path: '/compte/playtests.html?surface=web',
  },
  {
    label: 'Mes licences',
    description: 'Consulter les licences et droits numériques associés au compte sans les reproduire localement.',
    path: '/compte/licences.html?surface=web',
  },
  {
    label: 'Ressources privées',
    description: 'Ouvrir les documents autorisés par le serveur sans télécharger ni indexer leur inventaire dans ce hub.',
    path: '/compte/documents.html?surface=web',
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

export function NativeLibraryHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Ma bibliothèque</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun rôle, droit d’accès, licence, progression de lecture, candidature ou invitation de playtest, document privé ni inventaire de projet. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Les droits restent côté serveur</Text>
        <Text style={styles.boundaryText}>
          Le natif ne décide jamais si un projet, un document, un roman ou un produit est accessible. Les droits réels du compte, y compris les rôles propriétaire ou administrateur, restent évalués par les mécanismes Web et serveur existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>AUCUN SUIVI LOCAL</Text>
        <Text style={styles.boundaryTitle}>La progression de lecture n’est pas copiée</Text>
        <Text style={styles.boundaryText}>
          Ce sas ne reçoit ni page courante, ni pourcentage, ni dernière ouverture. Il ne produit aucun historique local de lecture et ne déduit pas vos intérêts à partir de votre bibliothèque.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PLAYTESTS PROTÉGÉS</Text>
        <Text style={styles.boundaryTitle}>Aucune admissibilité jeunesse ou invitation dans le natif</Text>
        <Text style={styles.boundaryText}>
          Les candidatures, invitations, acceptations, refus, participations et vérifications d’admissibilité restent côté Web/serveur. Ce sas ne reçoit aucune donnée d’âge, de tuteur, de cohorte jeunesse, de niveau d’accès ou de décision administrative.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>AUCUNE MUTATION</Text>
        <Text style={styles.boundaryTitle}>Aucune demande testeur depuis le natif</Text>
        <Text style={styles.boundaryText}>
          Le hub ne crée, ne modifie et n’annule aucune demande d’accès, licence, droit numérique ou participation de test. Toute action de ce type reste dans les surfaces authentifiées existantes.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>UNE SEULE SOURCE DE VÉRITÉ</Text>
        <Text style={styles.boundaryTitle}>Aucun cache d’inventaire privé</Text>
        <Text style={styles.boundaryText}>
          Les projets disponibles, documents autorisés, lectures, playtests et droits numériques ne sont ni dupliqués ni mis en cache par ce composant React Native.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les contenus, droits et décisions restent dans leurs surfaces protégées. Le natif ne conserve aucun résumé local de votre bibliothèque ou de vos participations testeur.
      </Text>
      <View style={styles.destinationList}>
        {libraryDestinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Votre bibliothèque n’est pas un profil comportemental</Text>
        <Text style={styles.privacyText}>
          SINJIRA utilise les informations de bibliothèque pour fournir les accès demandés. Ce sas ne les transforme pas en classement, recommandation ou signal de surveillance.
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
