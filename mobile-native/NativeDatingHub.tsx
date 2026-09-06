import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const datingDestinations = [
  {
    label: 'Ouvrir Rencontres',
    description: 'Continuer dans la surface Web privée qui applique l’admissibilité 18+, l’anonymisation, les consentements et les règles de sécurité.',
    path: '/compte/rencontres.html?surface=web',
  },
  {
    label: 'Comptes bloqués',
    description: 'Gérer vos blocages dans la surface sociale protégée existante.',
    path: '/compte/blocages.html',
  },
  {
    label: 'Règles de la communauté',
    description: 'Lire les règles de respect, de consentement, de confidentialité et de modération.',
    path: '/compte/regles-communaute.html',
  },
  {
    label: 'Ma sécurité',
    description: 'Ouvrir le Centre de sécurité du compte sans utiliser ses données pour calculer une compatibilité.',
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

export function NativeDatingHub({ onOpenPath, onBack }: Props) {
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
        <Text style={styles.title}>Rencontres</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun profil Rencontres, aucune préférence, aucun score de compatibilité, aucune proposition, aucune conversation et aucun compteur de messages. Il sert uniquement à vous orienter vers les protections Web existantes.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun choix relationnel n’est fait dans le natif</Text>
        <Text style={styles.boundaryText}>
          Le natif ne calcule, ne classe et ne recommande aucune personne. Il ne lit ni identité de genre, ni tranche d’âge recherchée, ni région, ni valeurs, ni limites personnelles, ni statut relationnel.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>CONSENTEMENT EXPLICITE</Text>
        <Text style={styles.boundaryTitle}>Le seuil 10 + 10 ne déclenche rien ici</Text>
        <Text style={styles.boundaryText}>
          Le seuil 10 + 10 ne déclenche rien dans le natif. Aucun consentement de dévoilement n’est enregistré ici, et aucun pseudo ou photo n’est révélé automatiquement. Le dévoilement reste une décision mutuelle appliquée par la surface Web et le serveur.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>SÉPARATION DES ESPACES</Text>
        <Text style={styles.boundaryTitle}>Le Registre reste séparé</Text>
        <Text style={styles.boundaryText}>
          Aucune donnée du Registre personnel n’est importée dans ce hub. L’option volontaire qui existe dans Rencontres reste entièrement contrôlée dans la surface Web et ne transfère jamais les données sensibles du Registre.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Le natif n’envoie aucun signalement, ne bloque aucun compte et ne prépare aucune rencontre publique. Ces actions restent derrière leurs contrôles Web et serveur.
      </Text>
      <View style={styles.destinationList}>
        {datingDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => onOpenPath(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Admissibilité et sécurité restent côté serveur</Text>
        <Text style={styles.privacyText}>
          Ce hub ne vérifie ni l’âge, ni le statut célibataire, ni l’admissibilité et ne conserve aucune préférence. Les contrôles 18+, l’anonymisation, les limites de contact, les signalements, les blocages, les Points SINJIRA et la préparation d’une rencontre publique restent dans leurs mécanismes protégés existants.
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
