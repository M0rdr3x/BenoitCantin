import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const communityDestinations = [
  {
    label: 'Communauté réelle',
    description: 'Ouvrir le réseau de profil existant. Les règles, l’identité affichée, le fil et la modération restent côté Web/serveur.',
    path: '/compte/communaute.html?surface=web',
  },
  {
    label: 'Mes commentaires',
    description: 'Consulter vos commentaires et leur état de modération dans la surface Web sans copier ici leur contenu ou leur statut.',
    path: '/compte/mes-commentaires.html?surface=web',
  },
  {
    label: 'Réseau personnage',
    description: 'Ouvrir le réseau rôle-play sans relier ici votre identité réelle au personnage ni rendre le rôle-play canonique.',
    path: '/compte/reseau-personnage.html?surface=web',
  },
  {
    label: 'Règles de la communauté',
    description: 'Lire ou accepter la version courante des règles dans la surface Web officielle. Ce hub ne mémorise pas votre acceptation.',
    path: '/compte/regles-communaute.html?surface=web',
  },
  {
    label: 'Sécurité et blocages',
    description: 'Gérer les protections sociales dans la surface de sécurité existante sans exposer localement les personnes bloquées ou signalées.',
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

export function NativeCommunityHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Communauté</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun profil communautaire, pseudo, publication, commentaire, réaction, blocage, signalement, état de modération ni acceptation des règles. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun fil social dans le natif</Text>
        <Text style={styles.boundaryText}>
          Le sas ne charge pas le fil, les auteurs, avatars, réactions ou commentaires. Il ne construit aucun historique local de vos lectures, interactions ou relations communautaires.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>DEUX IDENTITÉS SÉPARÉES</Text>
        <Text style={styles.boundaryTitle}>Profil réel et personnage ne sont jamais fusionnés ici</Text>
        <Text style={styles.boundaryText}>
          La Communauté réelle utilise l’identité de profil autorisée; le Réseau personnage utilise la représentation fictive. Ce hub ne reçoit aucun identifiant permettant de relier publiquement ces couches et ne transforme jamais le rôle-play en canon.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>RÈGLES AVANT INTERACTION</Text>
        <Text style={styles.boundaryTitle}>L’acceptation reste vérifiée côté Web</Text>
        <Text style={styles.boundaryText}>
          Le natif ne sait pas si vous avez accepté la version courante des règles et ne peut pas l’accepter à votre place. La surface communautaire authentifiée conserve cette vérification avant publication ou messagerie.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>MODÉRATION SANS EXPOSITION</Text>
        <Text style={styles.boundaryTitle}>Aucun état de commentaire n’est reconstruit localement</Text>
        <Text style={styles.boundaryText}>
          Ce hub ne lit ni le contenu de vos commentaires ni leur état en attente, publié ou refusé. Il ne signale, ne bloque, ne débloque et ne modère personne; motifs, preuves, cibles et statuts restent dans les mécanismes Web/serveur prévus pour protéger les personnes.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les identités, contenus et décisions sociales restent dans leurs surfaces existantes. Ce hub ne conserve aucun résumé local de votre activité communautaire.
      </Text>
      <View style={styles.destinationList}>
        {communityDestinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Une communauté n’est pas un graphe à surveiller</Text>
        <Text style={styles.privacyText}>
          SINJIRA doit permettre l’échange et la protection sans transformer vos interactions sociales en profil implicite. Ce sas n’analyse ni vos relations, ni vos réactions, ni les personnes que vous consultez.
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
