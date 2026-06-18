import { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Typography, GlassCard, SquishyButton, ScreenLayout } from '../../components/ui';
import { LinearGradient } from 'expo-linear-gradient';
import { auth, db } from '../../lib/firebaseClient';
import { doc, getDoc } from 'firebase/firestore';
import { COLORS, SPACING, TYPOGRAPHY, BORDER_RADIUS, GRADIENTS } from '../../theme';

export default function GameResultsScreen({ route, navigation }: any) {
  const { gameId, gameTitle, score, maxScore, xpEarned, completed, responses, achievements } = route.params || {
    gameId: 'sample-game',
    gameTitle: 'Sample Game',
    score: 85,
    maxScore: 100,
    xpEarned: 50,
    completed: true,
    responses: [],
    achievements: []
  };
  
  const [userData, setUserData] = useState<any>(null);
  const [partnerData, setPartnerData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        const user = auth.currentUser;
        if (user) {
          // Fetch user profile
          const userRef = doc(db, 'profiles', user.uid);
          const userSnap = await getDoc(userRef);
          
          if (userSnap.exists()) {
            setUserData(userSnap.data());
          }
          
          // Fetch couple data if linked
          if (userSnap.data()?.partner_id) {
            const partnerRef = doc(db, 'profiles', userSnap.data().partner_id);
            const partnerSnap = await getDoc(partnerRef);
            
            if (partnerSnap.exists()) {
              setPartnerData(partnerSnap.data());
            }
          }
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const percentage = Math.round((score / maxScore) * 100);
  const badgeColor = percentage >= 80 ? COLORS.success : percentage >= 60 ? COLORS.warning : COLORS.error;

  const renderAchievement = (achievement: any) => (
    <GlassCard key={achievement.id} style={styles.achievementCard}>
      <LinearGradient
        colors={[COLORS.vibrantPink + '33', COLORS.rosePink + '33']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.achievementGradient}
      >
        <View style={styles.achievementContent}>
          <Typography variant="h2" color={COLORS.textPrimary}>
            {achievement.title}
          </Typography>
          <Typography variant="caption" color={COLORS.textSecondary}>
            {achievement.description}
          </Typography>
        </View>
      </LinearGradient>
    </GlassCard>
  );

  return (
    <ScreenLayout showHeader={false} scrollable={true}>
      <LinearGradient
        colors={[COLORS.backgroundPrimary, COLORS.backgroundCard, COLORS.backgroundPrimary]}
        style={styles.gradient}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <Typography variant="h1" style={styles.title}>Game Results</Typography>
            <Typography variant="body" color={COLORS.textSecondary}>{gameTitle}</Typography>
          </View>

          <GlassCard style={styles.resultsCard}>
            <LinearGradient
              colors={[COLORS.vibrantPink + '33', COLORS.rosePink + '33']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.gradientContainer}
            >
              <View style={styles.scoreContainer}>
                <Typography variant="h1" color={badgeColor}>
                  {percentage}%
                </Typography>
                <Typography variant="body" color={COLORS.textSecondary} style={styles.scoreLabel}>
                  {score}/{maxScore} points
                </Typography>
              </View>

              <View style={styles.xpContainer}>
                <Typography variant="body" color={COLORS.textSecondary}>
                  XP Earned:
                </Typography>
                <Typography variant="h2" color={COLORS.aquaTeal} style={styles.xpValue}>
                  +{xpEarned}
                </Typography>
              </View>

              <View style={styles.badgeContainer}>
                <LinearGradient
                  colors={[badgeColor, badgeColor + '80']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.badgeGradient}
                >
                  <Typography variant="h2" color={COLORS.backgroundPrimary} center>
                    {percentage >= 80 ? 'EXCELLENT' : percentage >= 60 ? 'GOOD' : 'KEEP GOING'}
                  </Typography>
                </LinearGradient>
              </View>
            </LinearGradient>
          </GlassCard>

          {achievements && achievements.length > 0 && (
            <View>
              <Typography variant="h2" style={styles.sectionTitle}>Achievements</Typography>
              {achievements.map(renderAchievement)}
            </View>
          )}

          <View style={styles.statsContainer}>
            <GlassCard style={styles.statCard}>
              <LinearGradient
                colors={[COLORS.vibrantPink + '33', COLORS.rosePink + '33']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.gradientContainer}
              >
                <Typography variant="body" color={COLORS.textSecondary} style={styles.statLabel}>
                  Responses
                </Typography>
                <Typography variant="h2" color={COLORS.textPrimary}>
                  {responses ? responses.length : 0}
                </Typography>
              </LinearGradient>
            </GlassCard>

            <GlassCard style={styles.statCard}>
              <LinearGradient
                colors={[COLORS.vibrantPink + '33', COLORS.rosePink + '33']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.gradientContainer}
              >
                <Typography variant="body" color={COLORS.textSecondary} style={styles.statLabel}>
                  Completion
                </Typography>
                <Typography variant="h2" color={COLORS.textPrimary}>
                  {completed ? 'Yes' : 'No'}
                </Typography>
              </LinearGradient>
            </GlassCard>

            <GlassCard style={styles.statCard}>
              <LinearGradient
                colors={[COLORS.vibrantPink + '33', COLORS.rosePink + '33']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.gradientContainer}
              >
                <Typography variant="body" color={COLORS.textSecondary} style={styles.statLabel}>
                  Time
                </Typography>
                <Typography variant="h2" color={COLORS.textPrimary}>
                  5:42
                </Typography>
              </LinearGradient>
            </GlassCard>
          </View>

          <View style={styles.buttonContainer}>
            <SquishyButton 
              onPress={() => navigation.navigate('GameLibraryGridView')}
              style={styles.button}
            >
              <Typography variant="body">Play Another Game</Typography>
            </SquishyButton>

            <SquishyButton 
              onPress={() => navigation.navigate('DashboardHome')}
              variant="ghost"
              style={styles.secondaryButton}
            >
              <Typography variant="body">Return to Dashboard</Typography>
            </SquishyButton>
          </View>
        </ScrollView>
      </LinearGradient>
    </ScreenLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  content: {
    padding: SPACING.screenPadding,
    paddingBottom: SPACING.xxlarge,
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xlarge,
  },
  title: {
    marginBottom: SPACING.small,
  },
  resultsCard: {
    marginBottom: SPACING.xlarge,
  },
  gradientContainer: {
    padding: SPACING.regular,
    borderRadius: BORDER_RADIUS.xlarge,
    alignItems: 'center',
  },
  scoreContainer: {
    alignItems: 'center',
    marginBottom: SPACING.xlarge,
  },
  scoreLabel: {
    marginTop: SPACING.small,
  },
  xpContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.xlarge,
  },
  xpValue: {
    marginLeft: SPACING.small,
  },
  badgeContainer: {
    alignSelf: 'center',
    marginTop: SPACING.regular,
  },
  badgeGradient: {
    paddingHorizontal: SPACING.xlarge,
    paddingVertical: SPACING.regular,
    borderRadius: BORDER_RADIUS.xlarge,
  },
  sectionTitle: {
    color: COLORS.textPrimary,
    marginBottom: SPACING.regular,
  },
  achievementCard: {
    marginBottom: SPACING.regular,
  },
  achievementGradient: {
    padding: SPACING.regular,
    borderRadius: BORDER_RADIUS.xlarge,
  },
  achievementContent: {
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.xlarge,
  },
  statCard: {
    flex: 1,
    marginHorizontal: SPACING.tiny,
  },
  statLabel: {
    marginBottom: SPACING.small,
  },
  buttonContainer: {
    marginTop: SPACING.xlarge,
  },
  button: {
    marginBottom: SPACING.regular,
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
});
