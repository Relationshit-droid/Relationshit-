import { useEffect, useState } from 'react';
import { View, TextInput, StyleSheet, ActivityIndicator } from 'react-native';
import { GlassCard, Typography, SquishyButton, RadialGradientBackground } from '../../components/ui';
import { ScreenLayout } from '../../layout';
import { supabase, getProfile, linkPartnersTransactional, subscribeCouple } from '../../lib/supabase';
import { COLORS, TYPOGRAPHY, SPACING, BORDER_RADIUS } from '../../theme';

type PartnerEntryScreenProps = {
  onLinked: (code: string) => void;
};

export default function PartnerEntryScreen({ onLinked }: PartnerEntryScreenProps) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [comment, setComment] = useState('Waiting for partner...');

  useEffect(() => {
    let sub: any;
    if (code.startsWith('LA-') && code.endsWith('-LOVE')) {
      subscribeCouple(code, async () => {
        const { data } = await supabase.auth.getSession();
        const user = data.session?.user;
        if (!user) return;
        const me = await getProfile(user.id);
        const partnerId = me.data?.partner_id;
        if (partnerId) {
          setComment('Syncing stories...');
          setTimeout(() => onLinked(code), 800);
        }
      }).then((c) => (sub = c));
    }
    return () => { if (sub) supabase.removeChannel(sub); };
  }, [code]);

  async function validate() {
    setLoading(true);
    const { data } = await supabase.auth.getSession();
    const user = data.session?.user;
    if (!user) { setLoading(false); return; }
    const partner = await supabase.from('profiles').select('*').eq('couple_code', code).not('user_id', 'eq', user.id).limit(1);
    const partnerId = partner.data?.[0]?.user_id;
    if (partnerId) {
      try {
        await linkPartnersTransactional(user.id, partnerId, code);
      } catch (e) {
        setComment('Linking failed. Try again or refresh.');
        setLoading(false);
        return;
      }
      setComment('Linked! Dr. Marcie approves... for now.');
      setTimeout(() => onLinked(code), 800);
    } else {
      setComment('Code not found. Did you share the right tea?');
    }
    setLoading(false);
  }

  return (
    <ScreenLayout showHeader={false} scrollable={false}>
      <RadialGradientBackground />
      <View style={styles.content}>
        <GlassCard variant="elevated">
          <Typography variant="header">Enter Partner Code</Typography>
          <TextInput 
            value={code} 
            onChangeText={setCode} 
            placeholder="LA-XXXX-LOVE" 
            style={styles.input}
            placeholderTextColor={COLORS.textHint}
          />
          <Typography variant="marcieDialogue" style={styles.comment}>{comment}</Typography>
        </GlassCard>
        <SquishyButton onPress={validate}>
          {loading ? <ActivityIndicator color={COLORS.textPrimary} /> : <Typography variant="button">Validate</Typography>}
        </SquishyButton>
      </View>
    </ScreenLayout>
  );
}

const styles = StyleSheet.create({
  content: {
    flex: 1,
    padding: SPACING.screenPadding,
    justifyContent: 'center',
    gap: SPACING.regular,
  },
  input: { 
    backgroundColor: COLORS.backgroundInput, 
    borderWidth: 1, 
    borderColor: COLORS.borderSubtle, 
    borderRadius: BORDER_RADIUS.input, 
    padding: SPACING.regular, 
    color: COLORS.textPrimary,
    marginTop: SPACING.regular,
    fontSize: TYPOGRAPHY.fontSize.bodyLarge,
  },
  comment: {
    marginTop: SPACING.regular,
    color: COLORS.textSecondary,
  },
});
