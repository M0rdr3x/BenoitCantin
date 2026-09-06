import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const personalAiDestinations = [
  {
    label: 'Ouvrir Mon IA',
    description: 'Continuer dans la surface Web privée qui applique AAL2, le moteur de risque et les contrôles de consentement avant tout réglage.',
    path: '/compte/mon-ia.html?surface=web',
  },
  {
    label: 'Ma sécurité',
    description: 'Configurer ou vérifier les protections du compte avant d’accéder à un espace IA privé.',
    path: '/compte/securite.html',
  },
  {
    label: 'Histoire de vie',
    description: 'Gérer cet espace séparément. L’ouvrir ici n’accorde aucun accès à Mon IA.',
    path: '/compte/histoire-de-vie.html',
  },
  {
    label: 'Emploi',
    description: 'Gérer vos données professionnelles séparément. L’ouvrir ici ne crée aucun consentement IA.',
    path: '/compte/emploi.html?surface=web',
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

export function NativePersonalAiHub({ onOpenPath, onBack }: Props) {
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
        <Text style={styles.title}>Mon IA</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun réglage Mon IA, aucun consentement de source, aucun nom d’affichage, aucune langue, aucun audit et aucun état de sécurité. Il sert uniquement à vous orienter vers la surface privée existante.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucune opération privée n’est reproduite ici</Text>
        <Text style={styles.boundaryText}>
          Le natif n’ouvre pas vos réglages, ne change aucune préférence, n’accorde ou ne retire aucun consentement et ne supprime aucune donnée Mon IA. Toutes ces opérations restent derrière les contrôles Web et serveur existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>AAL2 TOUJOURS CÔTÉ SERVEUR</Text>
        <Text style={styles.boundaryTitle}>Le hub ne décide jamais si l’accès est autorisé</Text>
        <Text style={styles.boundaryText}>
          Ce composant n’évalue ni MFA, ni appareil, ni risque, ni challenge. L’exigence AAL2 et la ressource privée ai_private restent appliquées par les mécanismes d’authentification et de sécurité existants.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>AUCUN RUNTIME IA</Text>
        <Text style={styles.boundaryTitle}>Pas de chat, mémoire ou récupération de source</Text>
        <Text style={styles.boundaryText}>
          Le runtime V25 reste non configuré. Ce hub ne lance aucun modèle, ne stocke aucune conversation ou mémoire, ne récupère aucun contenu Histoire de vie ou Emploi et ne construit aucun profil psychologique.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>REGISTRE SÉPARÉ</Text>
        <Text style={styles.boundaryTitle}>Le Registre personnel n’est pas une source Mon IA</Text>
        <Text style={styles.boundaryText}>
          Aucune donnée du Registre personnel des consciences n’est importée dans ce hub et le Registre n’est jamais ajouté automatiquement comme source de Mon IA.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Ouvrir Histoire de vie ou Emploi depuis cet écran ne vaut jamais consentement pour Mon IA. Les autorisations de source restent explicites et séparées dans la surface privée Mon IA.
      </Text>
      <View style={styles.destinationList}>
        {personalAiDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Aucun clone IA</Text>
        <Text style={styles.privacyText}>
          Cette fondation ne crée aucun clone IA après le décès d’une personne. Le hub natif n’ajoute aucune capacité de ce type et ne devient pas une nouvelle source de données personnelles.
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
