import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeAlertsHub } from './NativeAlertsHub';
import { NativeMessagesHub } from './NativeMessagesHub';
import { NativeProfileHub } from './NativeProfileHub';

type Props = {
  onOpenPath: (path: string) => void;
  onOpenSecurity: () => void;
};

const mainDestinations = [
  {
    label: 'Messages',
    description: 'Ouvrir un hub natif sans contenu privé avant de choisir explicitement votre identité de messagerie.',
    path: '/compte/messages.html',
  },
  {
    label: 'Rencontres',
    description: 'Accéder au parcours Rencontres avec ses règles de sécurité et de consentement existantes.',
    path: '/compte/rencontres.html',
  },
  {
    label: 'Emploi',
    description: 'Ouvrir votre espace Emploi sans recopier votre profil ni vos candidatures dans le natif.',
    path: '/compte/emploi.html',
  },
  {
    label: 'Monde parallèle',
    description: 'Continuer votre parcours Monde dans la surface existante.',
    path: '/compte/monde-parallele.html',
  },
  {
    label: 'Mon IA',
    description: 'Ouvrir votre espace IA privé. Les protections renforcées restent appliquées avant tout accès sensible.',
    path: '/compte/mon-ia.html',
  },
] as const;

const accountDestinations = [
  {
    label: 'Alertes',
    description: 'Ouvrir un hub natif sans contenu privé avant vos avis SINJIRA.',
    path: '/compte/notifications.html',
  },
  {
    label: 'Profil',
    description: 'Ouvrir un hub natif sans données avant les réglages de profil existants.',
    path: '/compte/profil.html',
  },
  {
    label: 'Mode Voyage',
    description: 'Indiquer uniquement une destination approximative et une période pour la sécurité du compte.',
    path: '/compte/securite.html#travel-title',
  },
  {
    label: 'Registre personnel',
    description: 'Zone extrêmement sensible. Son ouverture conserve la vérification locale, le MFA et le moteur de risque.',
    path: '/compte/registre-personnel.html',
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

export function NativeHomeHub({ onOpenPath, onOpenSecurity }: Props) {
  const [alertsHubOpen, setAlertsHubOpen] = useState(false);
  const [messagesHubOpen, setMessagesHubOpen] = useState(false);
  const [profileHubOpen, setProfileHubOpen] = useState(false);

  if (messagesHubOpen) {
    return (
      <NativeMessagesHub
        onBack={() => setMessagesHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (alertsHubOpen) {
    return (
      <NativeAlertsHub
        onBack={() => setAlertsHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (profileHubOpen) {
    return (
      <NativeProfileHub
        onBack={() => setProfileHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  const openMainDestination = (path: string) => {
    if (path === '/compte/messages.html') {
      setMessagesHubOpen(true);
      return;
    }
    onOpenPath(path);
  };

  const openAccountDestination = (path: string) => {
    if (path === '/compte/notifications.html') {
      setAlertsHubOpen(true);
      return;
    }
    if (path === '/compte/profil.html') {
      setProfileHubOpen(true);
      return;
    }
    onOpenPath(path);
  };

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
        <Text style={styles.title}>Accueil</Text>
        <Text style={styles.intro}>
          Cet accueil natif sert uniquement à vous orienter. Il ne copie aucun message, profil, candidature, rencontre, confidence ni contenu privé depuis les services SINJIRA existants.
        </Text>
      </View>

      <View style={styles.securityCard}>
        <View style={styles.securityCopy}>
          <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
          <Text style={styles.securityTitle}>Ma sécurité</Text>
          <Text style={styles.securityText}>
            Ouvrez le hub natif pour la biométrie locale, les alertes et les raccourcis vers le Centre de sécurité.
          </Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Ouvrir le hub Ma sécurité"
          onPress={onOpenSecurity}
          style={styles.primaryButton}
        >
          <Text style={styles.primaryButtonText}>Ma sécurité</Text>
        </Pressable>
      </View>

      <Text style={styles.sectionTitle}>Continuer dans SINJIRA</Text>
      <Text style={styles.sectionText}>
        Les données et décisions restent dans leurs modules actuels. Cet écran ne garde aucun résumé local de votre activité.
      </Text>
      <View style={styles.destinationList}>
        {mainDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => openMainDestination(item.path)}
          />
        ))}
      </View>

      <Text style={styles.sectionTitle}>Compte et protection</Text>
      <View style={styles.destinationList}>
        {accountDestinations.map((item) => (
          <DestinationCard
            key={item.path}
            label={item.label}
            description={item.description}
            onPress={() => openAccountDestination(item.path)}
          />
        ))}
      </View>

      <View style={styles.privacyNote}>
        <Text style={styles.privacyTitle}>Une seule source de vérité</Text>
        <Text style={styles.privacyText}>
          La migration native se fait progressivement. Tant qu’un module n’est pas migré avec une frontière de sécurité équivalente, l’application ouvre sa surface existante plutôt que d’en créer une copie moins protégée.
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
  securityCard: { borderWidth: 1, borderColor: '#384260', borderRadius: 18, backgroundColor: '#10162a', padding: 15, gap: 12 },
  securityCopy: { gap: 5 },
  cardKicker: { color: '#91a0c7', fontSize: 10, fontWeight: '800', letterSpacing: 0.9 },
  securityTitle: { color: '#ffffff', fontSize: 19, fontWeight: '900' },
  securityText: { color: '#b8c2df', fontSize: 13, lineHeight: 19 },
  primaryButton: { alignSelf: 'flex-start', borderRadius: 10, backgroundColor: '#e4e9ff', paddingHorizontal: 14, paddingVertical: 10 },
  primaryButtonText: { color: '#10152a', fontWeight: '800', fontSize: 12 },
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
