import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onOpenSecurity: () => void;
  onOpenHome: () => void;
};

const accountDestinations = [
  {
    label: 'Ma bibliothèque',
    description: 'Ouvrir vos accès et lectures dans la surface SINJIRA existante.',
    path: '/compte/bibliotheque.html',
  },
  {
    label: 'Mon personnage',
    description: 'Retrouver votre personnage sans recopier son identité ni son état dans le natif.',
    path: '/compte/mon-personnage.html',
  },
  {
    label: 'Notifications',
    description: 'Consulter vos avis privés dans leur source de vérité existante.',
    path: '/compte/notifications.html',
  },
  {
    label: 'Messages',
    description: 'Ouvrir vos conversations sans en conserver de résumé dans ce hub.',
    path: '/compte/messages.html',
  },
  {
    label: 'Emploi',
    description: 'Accéder à votre profil professionnel privé et à vos candidatures sous leurs règles RLS existantes.',
    path: '/compte/emploi.html',
  },
  {
    label: 'Monde parallèle',
    description: 'Continuer votre parcours Monde dans la surface existante.',
    path: '/compte/monde-parallele.html',
  },
  {
    label: 'Communauté',
    description: 'Accéder à votre espace de participation avec votre identité de compte réelle.',
    path: '/compte/communaute.html',
  },
  {
    label: 'Rencontres',
    description: 'Ouvrir Rencontres avec les protections d’admissibilité, consentement et sécurité existantes.',
    path: '/compte/rencontres.html',
  },
] as const;

const identityDestinations = [
  {
    label: 'Profil',
    description: 'Modifier votre identité de profil et vos informations privées dans la surface serveur existante.',
    path: '/compte/profil.html',
  },
  {
    label: 'Paramètres',
    description: 'Gérer les préférences du compte sans les dupliquer dans ce hub.',
    path: '/compte/parametres.html',
  },
] as const;

const privateDestinations = [
  {
    label: 'Registre narratif',
    description: 'Questionnaire lié à l’univers de fiction. Il est distinct de votre coffre personnel réel.',
    path: '/projets/sinjira/registre/',
  },
  {
    label: 'Mon Registre personnel',
    description: 'Coffre réel extrêmement sensible, AAL2, séparé de la fiction et jamais transmis à vos proches.',
    path: '/compte/registre-personnel.html',
  },
  {
    label: 'Mon Histoire de vie',
    description: 'Souvenirs volontairement choisis pour votre histoire, séparés du Registre personnel.',
    path: '/compte/histoire-de-vie.html',
  },
  {
    label: 'Mon IA',
    description: 'Réglages et consentements privés. Aucun accès au Registre personnel et aucun runtime conversationnel configuré.',
    path: '/compte/mon-ia.html',
  },
] as const;

function DestinationCard({
  label,
  description,
  onPress,
}: {
  label: string;
  description: string;
  onPress: () => void;
}) {
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

export function NativeAccountHub({ onOpenPath, onOpenSecurity, onOpenHome }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Mon espace</Text>
        <Text style={styles.intro}>
          Ce hub natif remplace uniquement la navigation du tableau de compte. Il ne reçoit ni votre nom, ni votre courriel, ni votre avatar, ni vos compteurs, ni le contenu de vos notifications, parties, accès ou messages.
        </Text>
      </View>

      <View style={styles.actionRow}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Retourner à l’accueil SINJIRA"
          onPress={onOpenHome}
          style={styles.secondaryButton}
        >
          <Text style={styles.secondaryButtonText}>Accueil</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Ouvrir Ma sécurité"
          onPress={onOpenSecurity}
          style={styles.primaryButton}
        >
          <Text style={styles.primaryButtonText}>Ma sécurité</Text>
        </Pressable>
      </View>

      <Text style={styles.sectionTitle}>Compte et activités</Text>
      <Text style={styles.sectionText}>
        Les cartes ouvrent les modules existants; ce hub n’en extrait aucune donnée privée.
      </Text>
      <View style={styles.destinationList}>
        {accountDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <Text style={styles.sectionTitle}>Identité et préférences</Text>
      <View style={styles.destinationList}>
        {identityDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.sensitiveHeader}>
        <Text style={styles.sensitiveKicker}>ESPACES À NE PAS CONFONDRE</Text>
        <Text style={styles.sectionTitle}>Fiction, coffre réel et mémoire volontaire</Text>
        <Text style={styles.sectionText}>
          SINJIRA garde ces espaces séparés par conception. Le hub ne lit aucun de leurs contenus.
        </Text>
      </View>
      <View style={styles.destinationList}>
        {privateDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Aucun tableau privé recopié</Text>
        <Text style={styles.privacyText}>
          Le Web conserve la source de vérité pour les données de compte. React Native fournit ici une orientation plus directe, sans créer une seconde base, un cache de profil ou un résumé local de votre vie numérique.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#070914' },
  content: { padding: 16, paddingBottom: 28, gap: 16 },
  hero: { gap: 7 },
  eyebrow: { color: '#9ca8ca', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  title: { color: '#ffffff', fontSize: 30, fontWeight: '900' },
  intro: { color: '#bec7e4', fontSize: 14, lineHeight: 20 },
  actionRow: { flexDirection: 'row', gap: 10 },
  primaryButton: { borderRadius: 10, backgroundColor: '#e4e9ff', paddingHorizontal: 14, paddingVertical: 10 },
  primaryButtonText: { color: '#10152a', fontWeight: '800', fontSize: 12 },
  secondaryButton: { borderRadius: 10, borderWidth: 1, borderColor: '#384260', paddingHorizontal: 14, paddingVertical: 10 },
  secondaryButtonText: { color: '#e9edff', fontWeight: '800', fontSize: 12 },
  sectionTitle: { color: '#ffffff', fontSize: 19, fontWeight: '900' },
  sectionText: { color: '#aeb9d8', fontSize: 13, lineHeight: 19, marginTop: -10 },
  destinationList: { gap: 9 },
  destinationCard: { flexDirection: 'row', alignItems: 'center', gap: 12, borderWidth: 1, borderColor: '#252d45', backgroundColor: '#0e1427', borderRadius: 14, padding: 14 },
  destinationCopy: { flex: 1, gap: 4 },
  destinationTitle: { color: '#ffffff', fontSize: 15, fontWeight: '800' },
  destinationText: { color: '#aeb9d8', fontSize: 12, lineHeight: 18 },
  chevron: { color: '#dce3ff', fontSize: 28, fontWeight: '300' },
  sensitiveHeader: { gap: 7, borderTopWidth: 1, borderTopColor: '#27314d', paddingTop: 16 },
  sensitiveKicker: { color: '#d2b7ff', fontSize: 10, fontWeight: '900', letterSpacing: 1 },
  privacyNote: { borderRadius: 14, borderWidth: 1, borderColor: '#27314d', backgroundColor: '#0b1020', padding: 14, gap: 5 },
  privacyTitle: { color: '#eef1ff', fontSize: 14, fontWeight: '800' },
  privacyText: { color: '#aeb9d8', fontSize: 12, lineHeight: 18 },
});
