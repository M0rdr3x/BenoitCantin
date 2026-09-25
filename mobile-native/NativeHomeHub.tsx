import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeAlertsHub } from './NativeAlertsHub';
import { NativeCharacterHub } from './NativeCharacterHub';
import { NativeCharacterNetworkHub } from './NativeCharacterNetworkHub';
import { NativeCommerceHub } from './NativeCommerceHub';
import { NativeCommunityHub } from './NativeCommunityHub';
import { NativeDatingHub } from './NativeDatingHub';
import { NativeEmploymentHub } from './NativeEmploymentHub';
import { NativeGamesHub } from './NativeGamesHub';
import { NativeLibraryHub } from './NativeLibraryHub';
import { NativeLifeStoryHub } from './NativeLifeStoryHub';
import { NativeMessagesHub } from './NativeMessagesHub';
import { NativeParallelWorldHub } from './NativeParallelWorldHub';
import { NativePersonalAiHub } from './NativePersonalAiHub';
import { NativeProfileHub } from './NativeProfileHub';
import { NativeRelationsHub } from './NativeRelationsHub';

type Props = {
  onOpenPath: (path: string) => void;
  onOpenSecurity: () => void;
  accountMode: 'unknown' | 'child' | 'nonchild';
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
    label: 'Ma bibliothèque',
    description: 'Ouvrir un hub natif sans rôle, licence, progression ni droit d’accès avant la bibliothèque protégée.',
    path: '/compte/bibliotheque.html',
  },
  {
    label: 'Mes parties',
    description: 'Ouvrir un hub natif sans sauvegarde, code de partie, feuille de joueur ni fichier JSON local.',
    path: '/compte/mes-parties.html',
  },
  {
    label: 'Communauté',
    description: 'Ouvrir un hub natif sans identité, fil social, réaction, signalement ni état de modération.',
    path: '/compte/communaute.html',
  },
  {
    label: 'Réseau personnage',
    description: 'Ouvrir un hub natif sans identité réelle, graphe social, publication, réaction, groupe ni rôle propriétaire local.',
    path: '/compte/reseau-personnage.html',
  },
  {
    label: 'Relations et famille',
    description: 'Ouvrir un hub natif sans relation privée, tranche d’âge, code parental ni lien de supervision local.',
    path: '/compte/relations.html',
  },
  {
    label: 'Commerce et droits',
    description: 'Ouvrir un hub natif sans achat, précommande, annonce, solde de jetons, licence ni donnée transactionnelle locale.',
    path: '/compte/mes-achats.html',
  },
  {
    label: 'Mon personnage',
    description: 'Ouvrir un hub natif sans fiche humaine, portrait, bible narrative ni statut avant la surface personnage protégée.',
    path: '/compte/mon-personnage.html',
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

const childDestinations = [
  {
    label: 'Communauté Junior',
    description: 'Espace 11–12 ans séparé, pseudonymisé et sans messages privés.',
    path: '/compte/communaute-junior.html',
  },
  {
    label: 'Bibliothèque Junior',
    description: 'Voir uniquement les projets et documents approuvés explicitement pour les 11–12 ans.',
    path: '/compte/bibliotheque.html',
  },
  {
    label: 'Profil',
    description: 'Ouvrir les réglages du compte sans utiliser le profil comme identité publique dans la Communauté Junior.',
    path: '/compte/profil.html',
  },
  {
    label: 'Relations et famille',
    description: 'Voir le lien parent ou tuteur et les réglages de supervision sans surveillance du contenu.',
    path: '/compte/relations.html',
  },
] as const;

const unverifiedDestinations = [
  {
    label: 'Vérifier mon compte',
    description: 'Ouvrir le compte Web sécurisé pour déterminer les accès autorisés avant d’activer les hubs natifs.',
    path: '/compte/index.html',
  },
  {
    label: 'Profil',
    description: 'Ouvrir la surface Web protégée. Si une connexion est requise, SINJIRA la demandera avant tout contenu privé.',
    path: '/compte/profil.html',
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

export function NativeHomeHub({ onOpenPath, onOpenSecurity, accountMode }: Props) {
  const [alertsHubOpen, setAlertsHubOpen] = useState(false);
  const [characterHubOpen, setCharacterHubOpen] = useState(false);
  const [characterNetworkHubOpen, setCharacterNetworkHubOpen] = useState(false);
  const [commerceHubOpen, setCommerceHubOpen] = useState(false);
  const [communityHubOpen, setCommunityHubOpen] = useState(false);
  const [datingHubOpen, setDatingHubOpen] = useState(false);
  const [employmentHubOpen, setEmploymentHubOpen] = useState(false);
  const [gamesHubOpen, setGamesHubOpen] = useState(false);
  const [libraryHubOpen, setLibraryHubOpen] = useState(false);
  const [lifeStoryHubOpen, setLifeStoryHubOpen] = useState(false);
  const [messagesHubOpen, setMessagesHubOpen] = useState(false);
  const [parallelWorldHubOpen, setParallelWorldHubOpen] = useState(false);
  const [personalAiHubOpen, setPersonalAiHubOpen] = useState(false);
  const [profileHubOpen, setProfileHubOpen] = useState(false);
  const [relationsHubOpen, setRelationsHubOpen] = useState(false);

  if (accountMode !== 'nonchild') {
    const isChild = accountMode === 'child';
    const destinations = isChild ? childDestinations : unverifiedDestinations;
    return (
      <ScrollView style={styles.root} contentContainerStyle={styles.content}>
        <View style={styles.hero}>
          <Text style={styles.eyebrow}>L’HUMAIN AVANT TOUT</Text>
          <Text style={styles.title}>{isChild ? 'Accueil Junior' : 'Accueil protégé'}</Text>
          <Text style={styles.intro}>
            {isChild
              ? 'Le mode Junior n’affiche que des destinations compatibles avec les comptes de 11–12 ans. Les hubs adultes restent fermés.'
              : 'Avant d’ouvrir les hubs natifs, SINJIRA vérifie la catégorie d’accès du compte dans la surface Web authentifiée. Aucun âge exact, courriel ou identifiant utilisateur n’est transmis au shell natif.'}
          </Text>
        </View>

        <View style={styles.securityCard}>
          <View style={styles.securityCopy}>
            <Text style={styles.cardKicker}>PROTÉGER SANS SURVEILLER</Text>
            <Text style={styles.securityTitle}>Ma sécurité</Text>
            <Text style={styles.securityText}>
              La biométrie reste sur le téléphone. Les accès du compte sont vérifiés par le site avant qu’un module natif sensible soit proposé.
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

        <View style={styles.transparencyCard}>
          <Text style={styles.transparencyKicker}>TRANSPARENCE IA</Text>
          <Text style={styles.transparencyTitle}>Les idées et décisions restent humaines</Text>
          <Text style={styles.transparencyText}>
            Idées, vision et décisions : Benoit Cantin. Des outils d’intelligence artificielle peuvent aider à la mise en œuvre; la validation finale et la responsabilité du contenu restent humaines.
          </Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Lire la déclaration de transparence sur l’intelligence artificielle"
            onPress={() => onOpenPath('/transparence-ia.html')}
            style={styles.transparencyButton}
          >
            <Text style={styles.transparencyButtonText}>Lire la déclaration</Text>
          </Pressable>
        </View>

        <Text style={styles.sectionTitle}>{isChild ? 'Mon espace 11–12 ans' : 'Vérification du compte'}</Text>
        <Text style={styles.sectionText}>
          {isChild
            ? 'Les destinations générales Messages, Rencontres, Emploi, Monde parallèle, Mon IA, commerce et playtests ne sont pas affichées.'
            : 'Tant que le compte n’est pas vérifié, le mobile reste fail-closed et n’affiche pas les destinations sensibles.'}
        </Text>
        <View style={styles.destinationList}>
          {destinations.map((item) => (
            <DestinationCard
              key={item.path}
              label={item.label}
              description={item.description}
              onPress={() => onOpenPath(item.path)}
            />
          ))}
        </View>

        <View style={styles.privacyNote}>
          <Text style={styles.privacyTitle}>État minimal uniquement</Text>
          <Text style={styles.privacyText}>
            Le shell natif reçoit seulement « Junior », « non-Junior » ou « inconnu ». Il ne reçoit ni date de naissance, ni identité, ni contenu privé pour décider quels raccourcis afficher.
          </Text>
        </View>
      </ScrollView>
    );
  }

  if (characterHubOpen) {
    return (
      <NativeCharacterHub
        onBack={() => setCharacterHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (characterNetworkHubOpen) {
    return (
      <NativeCharacterNetworkHub
        onBack={() => setCharacterNetworkHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (commerceHubOpen) {
    return (
      <NativeCommerceHub
        onBack={() => setCommerceHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (communityHubOpen) {
    return (
      <NativeCommunityHub
        onBack={() => setCommunityHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

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

  if (gamesHubOpen) {
    return (
      <NativeGamesHub
        onBack={() => setGamesHubOpen(false)}
        onOpenPath={onOpenPath}
      />
    );
  }

  if (libraryHubOpen) {
    return (
      <NativeLibraryHub
        onBack={() => setLibraryHubOpen(false)}
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

  if (relationsHubOpen) {
    return (
      <NativeRelationsHub
        onBack={() => setRelationsHubOpen(false)}
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
    if (path === '/compte/bibliotheque.html') {
      setLibraryHubOpen(true);
      return;
    }
    if (path === '/compte/mes-parties.html') {
      setGamesHubOpen(true);
      return;
    }
    if (path === '/compte/communaute.html') {
      setCommunityHubOpen(true);
      return;
    }
    if (path === '/compte/reseau-personnage.html') {
      setCharacterNetworkHubOpen(true);
      return;
    }
    if (path === '/compte/relations.html') {
      setRelationsHubOpen(true);
      return;
    }
    if (path === '/compte/mes-achats.html') {
      setCommerceHubOpen(true);
      return;
    }
    if (path === '/compte/mon-personnage.html') {
      setCharacterHubOpen(true);
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

      <View style={styles.transparencyCard}>
        <Text style={styles.transparencyKicker}>TRANSPARENCE IA</Text>
        <Text style={styles.transparencyTitle}>Les idées et décisions restent humaines</Text>
        <Text style={styles.transparencyText}>
          Idées, vision et décisions : Benoit Cantin. Des outils d’intelligence artificielle peuvent aider à la mise en œuvre; la validation finale et la responsabilité du contenu restent humaines.
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Lire la déclaration de transparence sur l’intelligence artificielle"
          onPress={() => onOpenPath('/transparence-ia.html')}
          style={styles.transparencyButton}
        >
          <Text style={styles.transparencyButtonText}>Lire la déclaration</Text>
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
  transparencyCard: { borderWidth: 1, borderColor: '#2d746f', borderRadius: 18, backgroundColor: '#0d1d24', padding: 15, gap: 6 },
  transparencyKicker: { color: '#91f8ee', fontSize: 10, fontWeight: '900', letterSpacing: 1.1 },
  transparencyTitle: { color: '#ffffff', fontSize: 17, fontWeight: '900' },
  transparencyText: { color: '#c5d9dc', fontSize: 13, lineHeight: 19 },
  transparencyButton: { alignSelf: 'flex-start', marginTop: 5, borderRadius: 10, borderWidth: 1, borderColor: '#4d9992', paddingHorizontal: 12, paddingVertical: 9 },
  transparencyButtonText: { color: '#bafef7', fontSize: 12, fontWeight: '800' },
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
