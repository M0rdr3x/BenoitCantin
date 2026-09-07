import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  onOpenPath: (path: string) => void;
  onBack: () => void;
};

const commerceDestinations = [
  {
    label: 'Mes achats et précommandes',
    description: 'Ouvrir vos réservations et préférences dans la surface Web protégée. Aucun paiement n’est exécuté par ce hub.',
    path: '/compte/mes-achats.html?surface=web',
  },
  {
    label: 'Mes annonces',
    description: 'Ouvrir vos brouillons du Marché sans copier ici prix, description, état ou localisation approximative.',
    path: '/compte/marche.html?surface=web',
  },
  {
    label: 'Jetons',
    description: 'Consulter le grand livre côté Web sans exposer localement solde, mouvements, description ou statut propriétaire.',
    path: '/compte/jetons.html?surface=web',
  },
  {
    label: 'Licences',
    description: 'Consulter les droits numériques dans leur surface protégée sans les reconstruire dans le natif.',
    path: '/compte/licences.html?surface=web',
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

export function NativeCommerceHub({ onOpenPath, onBack }: Props) {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={onBack} style={styles.backButton}>
        <Text style={styles.backButtonText}>‹ Retour</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Commerce et droits</Text>
        <Text style={styles.intro}>
          Ce hub natif ne lit aucun solde de jetons, mouvement, achat, précommande, préférence de réception, annonce, prix, localisation, licence ou droit numérique. Il sert uniquement à vous orienter.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
        <Text style={styles.boundaryTitle}>Aucun profil d’achat local</Text>
        <Text style={styles.boundaryText}>
          Les réservations, formats souhaités, quantités, préférences de livraison ou ramassage et historiques commerciaux ne sont pas copiés dans React Native et ne servent pas à déduire vos moyens ou habitudes.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>PAIEMENTS</Text>
        <Text style={styles.boundaryTitle}>Aucun checkout ni moyen de paiement dans ce sas</Text>
        <Text style={styles.boundaryText}>
          Les achats payants restent désactivés dans les surfaces auditées. Ce composant ne prépare aucun paiement, ne recueille aucune carte, adresse de facturation ou adresse de livraison, et ne transforme jamais une précommande en commande.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>JETONS</Text>
        <Text style={styles.boundaryTitle}>Le grand livre reste côté serveur</Text>
        <Text style={styles.boundaryText}>
          Le hub ne connaît ni le solde, ni les mouvements, ni leur description, ni un éventuel statut propriétaire. Il ne crédite, ne débite et ne transfère aucun Jeton SINJIRA™.
        </Text>
      </View>

      <View style={styles.boundaryCard}>
        <Text style={styles.cardKicker}>MARCHÉ</Text>
        <Text style={styles.boundaryTitle}>Les brouillons et la localisation restent privés</Text>
        <Text style={styles.boundaryText}>
          Aucun titre, description, prix, état d’objet ou localisation approximative d’annonce n’est chargé ici. Le hub ne crée, ne publie et ne supprime aucune annonce.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Choisir une destination</Text>
      <Text style={styles.sectionText}>
        Les opérations commerciales et droits restent dans leurs surfaces authentifiées. Le natif ne conserve aucun résumé financier ou transactionnel.
      </Text>
      <View style={styles.destinationList}>
        {commerceDestinations.map((item) => (
          <DestinationCard key={item.path} label={item.label} description={item.description} onPress={() => onOpenPath(item.path)} />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Vos choix commerciaux ne définissent pas votre valeur</Text>
        <Text style={styles.privacyText}>
          Ce sas ne classe pas les personnes selon leurs achats, leurs annonces, leurs Jetons ou leurs licences. Les données nécessaires restent limitées aux fonctions demandées.
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
