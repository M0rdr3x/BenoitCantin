import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const gamesDestinations = [
  {
    label: 'Mes parties',
    description: 'Ouvrir vos sauvegardes dans la surface Web protégée sans copier ici leur contenu, leur état ou leurs codes.',
    path: '/compte/mes-parties.html?surface=web',
  },
  {
    label: 'Programme Contributeur',
    description: 'Gérer vos consentements de contribution dans la surface Web sans partager automatiquement une partie ou un commentaire libre.',
    path: '/compte/contributions.html?surface=web',
  },
  {
    label: 'Ma bibliothèque',
    description: 'Choisir un jeu depuis la bibliothèque Web sans reconstruire vos droits ou votre progression dans ce sas.',
    path: '/compte/bibliotheque.html?surface=web',
  },
  {
    label: 'Jeux SINJIRA',
    description: 'Parcourir le portail public des jeux sans transmettre une sauvegarde ou un historique privé.',
    path: '/projets/sinjira/jeux/',
  },
  {
    label: 'Ma sécurité',
    description: 'Ouvrir le Centre de sécurité existant sans exposer les données d’une partie.',
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

export function NativeGamesHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Mes parties</Text>
        <Text style={styles.intro}>
          Ce sas ne lit aucune partie, sauvegarde, code de partie, feuille de joueur, résultat de fin de partie ni fichier JSON. Il ne lit pas non plus vos préférences de contribution et sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun état de partie local</Text>
        <Text style={styles.boundaryText}>
          Le titre, le statut, la date de mise à jour, le jeu, le code de partie, les nombres de joueurs, le mode de jeu et la durée restent dans la surface Web et les services existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CONSENTEMENT EXPLICITE</Text>
        <Text style={styles.boundaryTitle}>Aucune contribution automatique</Text>
        <Text style={styles.boundaryText}>
          Ce hub ne sait pas si vous participez au Programme Contributeur, n’active aucun consentement et ne transmet aucune sauvegarde, statistique de partie ou commentaire libre. Ces choix restent volontaires et contrôlés dans la surface Web.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>SAUVEGARDES PRIVÉES</Text>
        <Text style={styles.boundaryTitle}>Les exports volontaires restent Web</Text>
        <Text style={styles.boundaryText}>
          Le natif ne fabrique, ne lit, ne partage et ne mémorise aucun fichier de sauvegarde. Les exports JSON privés restent déclenchés explicitement par la personne dans la surface Web.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>IMPORTS</Text>
        <Text style={styles.boundaryTitle}>Aucune création de partie depuis un fichier natif</Text>
        <Text style={styles.boundaryText}>
          Ce hub ne sélectionne, ne décode et n’importe aucun fichier. Il ne clone aucune session, ne génère aucun code de partie et n’écrit aucune feuille de joueur.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>FEUILLES PRIVÉES</Text>
        <Text style={styles.boundaryTitle}>Les feuilles de joueur restent hors du natif</Text>
        <Text style={styles.boundaryText}>
          Les feuilles de joueur et de fin de partie peuvent contenir l’état détaillé d’une sauvegarde. Elles ne sont ni affichées, ni résumées, ni mises en cache par ce sas.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        La Web et le serveur restent la source de vérité des parties et des consentements de contribution. Ce sas ne conserve aucun résumé local de votre historique de jeu.
      </Text>
      <View style={styles.destinationList}>
        {gamesDestinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Pas de profil de jeu</Text>
        <Text style={styles.privacyText}>
          L’historique de vos parties, votre temps de jeu, vos modes choisis et vos résultats ne servent pas ici à déduire votre valeur, vos capacités ou vos préférences.
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
