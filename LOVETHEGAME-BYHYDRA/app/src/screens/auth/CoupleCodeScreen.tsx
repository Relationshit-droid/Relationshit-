import { useEffect, useState, useRef } from 'react';
import { View, StyleSheet, TextInput, ScrollView, Animated as RNAnimated, Alert, ActivityIndicator } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { Typography, GlassCard, SquishyButton, RadialGradientBackground } from '../../components/ui';
import { ScreenLayout } from '../../layout';
import { supabase, upsertProfile, linkPartnersTransactional, subscribeCouple, getProfile } from '../../lib/supabase';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { COLORS, GRADIENTS, TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS } from '../../theme';

type CoupleCodeScreenProps = {
  onNext: (code: string) => void;
};

export default function CoupleCodeScreen({ onNext }: CoupleCodeScreenProps) {
  const [code, setCode] = useState(generateCoupleCode());
  const [partnerCode, setPartnerCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const inputs = useRef<Array<TextInput | null>>([]);
  const pulseAnim = useRef(new RNAnimated.Value(1)).current;

  useEffect(() => {
    let sub: any;

    const init = async () => {
      const { data } = await supabase.auth.getSession();
      const user = data.session?.user;
      if (user) {
        await upsertProfile({ user_id: user.id, couple_code: code });

        sub = await subscribeCouple(code, async () => {
          const me = await getProfile(user.id);
          if (me.data?.partner_id) {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            onNext(code);
          }
        });
      }
    };

    init();

    RNAnimated.loop(
      RNAnimated.sequence([
        RNAnimated.timing(pulseAnim, { toValue: 0.4, duration: 1500, useNativeDriver: true }),
        RNAnimated.timing(pulseAnim, { toValue: 1, duration: 1500, useNativeDriver: true })
      ])
    ).start();

    return () => { if (sub) supabase.removeChannel(sub); };
  }, [code]);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(code);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  const handlePartnerCodeChange = (text: string, index: number) => {
    if (text.length > 1) {
      const newCode = [...partnerCode];
      for (let i = 0; i < Math.min(text.length, 6 - index); i++) {
        newCode[index + i] = text[i];
      }
      setPartnerCode(newCode);
      if (index + text.length < 6) {
        inputs.current[index + text.length]?.focus();
      } else {
        inputs.current[index]?.blur();
      }
      return;
    }

    const newCode = [...partnerCode];
    newCode[index] = text;
    setPartnerCode(newCode);
    if (text && index < 5) {
      inputs.current[index + 1]?.focus();
    }
    if (!text && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const connectSignal = async () => {
    Haptics.selectionAsync();
    const fullCode = partnerCode.join('');
    if (fullCode.length !== 6) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Invalid Code', 'Please enter a full 6-digit code.');
      return;
    }

    setLoading(true);
    try {
      const { data } = await supabase.auth.getSession();
      const user = data.session?.user;
      if (!user) throw new Error('Not authenticated');

      const { data: partners, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('couple_code', fullCode)
        .neq('user_id', user.id);

      if (error || !partners || partners.length === 0) {
        throw new Error('Partner code not found. Check the code and try again.');
      }

      const partner = partners[0];
      await linkPartnersTransactional(user.id, partner.user_id, fullCode);

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onNext(fullCode);

    } catch (e: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Connection Failed', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenLayout showHeader={false} scrollable={false}>
      <RadialGradientBackground />
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <Typography variant="label" style={styles.headerTitle}>CONNECTION SYNC</Typography>
            <Typography variant="body" style={styles.phaseText}>PHASE 1 / 5</Typography>
          </View>
          <View style={styles.progressBar}>
            <LinearGradient colors={GRADIENTS.progress.colors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: '20%', height: '100%' }} />
          </View>
        </View>

        <View style={styles.titleSec}>
          <Typography variant="header" style={styles.mainTitle}>Couple Linking</Typography>
          <Typography variant="body" style={styles.subSubtitle}>Resonate your frequencies to begin.</Typography>
        </View>

        <View style={styles.cardsContainer}>
          <GlassCard style={styles.card} variant="elevated">
            <Ionicons name="wifi" size={32} color={COLORS.aquaTeal} style={{ alignSelf: 'center' }} />
            <Typography variant="label" style={styles.cardHeader}>YOUR FREQUENCY</Typography>
            <Typography variant="header" style={styles.codeDisplay}>{code}</Typography>
            <SquishyButton onPress={handleCopy}>
              <Ionicons name="copy-outline" size={18} color={COLORS.textPrimary} />
              <Typography variant="button" style={{ marginLeft: SPACING.small }}>COPY CODE</Typography>
            </SquishyButton>
          </GlassCard>

          <GlassCard style={styles.card} variant="elevated">
            <Ionicons name="link" size={32} color={COLORS.vibrantPink} style={{ alignSelf: 'center' }} />
            <Typography variant="label" style={styles.cardHeader}>ENTER PARTNER'S CODE</Typography>

            <View style={styles.inputRow}>
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <TextInput
                  key={i}
                  ref={r => { inputs.current[i] = r; }}
                  style={styles.codeDigit}
                  maxLength={1}
                  value={partnerCode[i]}
                  onChangeText={(t) => handlePartnerCodeChange(t, i)}
                  keyboardType="default"
                  autoCapitalize="characters"
                  placeholder="•"
                  placeholderTextColor={COLORS.textHint}
                  editable={!loading}
                />
              ))}
            </View>

            <SquishyButton onPress={connectSignal} disabled={loading}>
              {loading ? <ActivityIndicator color={COLORS.textPrimary} /> : (
                <>
                  <Typography variant="button">CONNECT SIGNAL</Typography>
                  <Ionicons name="heart" size={20} color={COLORS.vibrantPink} style={{ marginLeft: SPACING.small }} />
                </>
              )}
            </SquishyButton>
          </GlassCard>
        </View>

        <View style={styles.waiting}>
          <View style={styles.pulseContainer}>
            <View style={styles.dot} />
            <View style={[styles.dotPing, { position: 'absolute' }]} />
          </View>
          <RNAnimated.Text style={[styles.waitingText, { opacity: pulseAnim }]}>Waiting for Partner...</RNAnimated.Text>
        </View>

        <View style={{ height: SPACING.xxlarge }} />
      </ScrollView>
    </ScreenLayout>
  );
}

function generateCoupleCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const segment = () => new Array(6).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
  return segment();
}

const styles = StyleSheet.create({
  scroll: { 
    padding: SPACING.screenPadding 
  },
  header: { 
    marginBottom: SPACING.xlarge 
  },
  headerTop: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'flex-end', 
    marginBottom: SPACING.small 
  },
  headerTitle: { 
    color: COLORS.textSecondary 
  },
  phaseText: { 
    color: COLORS.aquaTeal 
  },
  progressBar: { 
    height: 4, 
    backgroundColor: COLORS.divider, 
    borderRadius: BORDER_RADIUS.small, 
    overflow: 'hidden' 
  },
  titleSec: { 
    alignItems: 'center', 
    marginBottom: SPACING.large 
  },
  mainTitle: { 
    fontSize: TYPOGRAPHY.fontSize.displayLarge 
  },
  subSubtitle: { 
    color: COLORS.textSecondary 
  },
  cardsContainer: { 
    gap: SPACING.large 
  },
  card: { 
    padding: SPACING.xlarge, 
    alignItems: 'center', 
    gap: SPACING.regular 
  },
  cardHeader: { 
    color: COLORS.textSecondary 
  },
  codeDisplay: { 
    fontSize: TYPOGRAPHY.fontSize.displayLarge, 
    color: COLORS.aquaTeal, 
    letterSpacing: 4 
  },
  inputRow: { 
    flexDirection: 'row', 
    gap: SPACING.small, 
    justifyContent: 'center' 
  },
  codeDigit: { 
    width: 40, 
    height: 50, 
    backgroundColor: COLORS.backgroundInput, 
    borderRadius: BORDER_RADIUS.medium, 
    borderWidth: 1, 
    borderColor: COLORS.borderSubtle, 
    color: COLORS.textPrimary, 
    fontSize: TYPOGRAPHY.fontSize.displaySmall, 
    textAlign: 'center', 
    fontWeight: 'bold' 
  },
  waiting: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    gap: SPACING.regular, 
    marginTop: SPACING.xxlarge, 
    opacity: 0.6 
  },
  waitingText: { 
    color: COLORS.textPrimary 
  },
  pulseContainer: { 
    width: 10, 
    height: 10, 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  dot: { 
    width: 10, 
    height: 10, 
    borderRadius: BORDER_RADIUS.round, 
    backgroundColor: COLORS.warmOrange 
  },
  dotPing: { 
    width: 10, 
    height: 10, 
    borderRadius: BORDER_RADIUS.round, 
    backgroundColor: COLORS.warmOrange, 
    opacity: 0.5 
  }
});
