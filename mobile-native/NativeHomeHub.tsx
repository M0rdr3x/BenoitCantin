import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeAlertsHub } from './NativeAlertsHub';
import { NativeDatingHub } from './NativeDatingHub';
import { NativeEmploymentHub } from './NativeEmploymentHub';
import { NativeLifeStoryHub } from './NativeLifeStoryHub';
import { NativeMessagesHub } from './NativeMessagesHub';
import { NativeParallelWorldHub } from './NativeParallelWorldHub';
import { NativePersonalAiHub } from './NativePersonalAiHub';
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
    description: 'Ouvrir un hub natif sans profil, compatibilité ni conversation avant la surface Rencontres protégée.',
    path: '/compte/rencontres.html',
  },
  {
    label: 'Emploi',
    description: 'Ouvrir un hub natif sans données professionnelles avant le profil et les candidatures protégés.',
    path: '/compte/emploi.html',
  },
  {
    label: 'Monde parallèle',
    description: 'Ouvrir un hub natif sans identité ni Chronique privée avant la continuité Monde parallèle protégée.',
    path: '/compte/monde-parallele.html',
  },
  {
    label: 'Mon IA',
    description: 'Ouvrir un hub natif sans réglage, consentement ni runtime avant la surface IA privée protégée.',
    path: '/compte/mon-ia.html',
  },
  {
    label: 'Histoire de vie',
    description: 'Ouvrir un hub natif sans souvenir, destinataire ni directive avant la surface Histoire de vie protégée.',
    path: '/compte/histoire-de-vie.html',
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
  const [datingHubOpen, setDatingHubOpen] = useState(false);
  const [employmentHubOpen, setEmploymentHubOpen] = useState(false);
  const [lifeStoryHubOpen, setLifeStoryHubOpen] = useState(false);
  const [messagesHubOpen, setMessagesHubOpen] = useState(false);
  const [parallelWorldHubOpen, setParallelWorldHubOpen] = useState(false);
  const [personalAiHubOpen, setPersonalAiHubOpen] = useState(false);
  const [profileHubOpen, setProfileHubOpen] = useState(false);

  if (datingHubOpen) {
    return (
      <NativeDatingHub
        onBack={() => setDatingHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (employmentHubOpen) {
    return (
      <NativeEmploymentHub
        onBack={() => setEmploymentHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (lifeStoryHubOpen) {
    return (
      <NativeLifeStoryHub
        onBack={() => setLifeStoryHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (parallelWorldHubOpen) {
    return (
      <NativeParallelWorldHub
        onBack={() => setParallelWorldHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (personalAiHubOpen) {
    return (
      <NativePersonalAiHub
        onBack={() => setPersonalAiHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

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
    if (path === '/compte/rencontres.html') {
      setDatingHubOpen(true);
      return;
    }
    if (path === '/compte/emploi.html') {
      setEmploymentHubOpen(true);
      return;
    }
    if (path === '/compte/monde-parallele.html') {
      setParallelWorldHubOpen(true);
      return;
    }
    if (path === '/compte/mon-ia.html') {
      setPersonalAiHubOpen(true);
      return;
    }
    if (path === '/compte/histoire-de-vie.html') {
      setLifeStoryHubOpen(true);
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
