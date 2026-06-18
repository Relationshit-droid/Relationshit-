import React, { useState } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { auth, db } from '../../lib/firebaseClient';
import { doc, getDoc, setDoc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { BlurView } from 'expo-blur';
import { ScreenLayout } from '../../layout';
import { Typography, SquishyButton, RadialGradientBackground, GlassCard } from '../../components/ui';
import { COLORS, GRADIENTS, SPACING, TYPOGRAPHY, BORDER_RADIUS, SHADOWS } from '../../theme';

const CoupleLinkingScreen = () => {
  const [partnerCode, setPartnerCode] = useState('');
  const navigation = useNavigation();

  const handleLinkCouple = async () => {
    if (!partnerCode.trim()) {
      Alert.alert('Error', 'Please enter a partner code');
      return;
    }

    try {
      const currentUser = auth.currentUser;
      if (!currentUser) {
        Alert.alert('Error', 'You must be logged in to link with a partner');
        return;
      }

      const partnerProfileRef = doc(db, 'profiles', partnerCode.toUpperCase());
      const partnerProfileSnap = await getDoc(partnerProfileRef);

      if (!partnerProfileSnap.exists()) {
        Alert.alert('Error', 'Invalid partner code. Please try again.');
        return;
      }

      const partnerData = partnerProfileSnap.data();
      const partnerUserId = partnerData.userId;

      if (partnerUserId === currentUser.uid) {
        Alert.alert('Error', 'You cannot link with yourself!');
        return;
      }

      if (partnerData.partnerId) {
        Alert.alert('Error', 'This partner is already linked to someone else.');
        return;
      }

      const coupleId = `${currentUser.uid}_${partnerUserId}`.split('').sort().join('');
      
      const currentUserProfileRef = doc(db, 'profiles', currentUser.uid);
      await updateDoc(currentUserProfileRef, {
        partnerId: partnerUserId,
        coupleId: coupleId,
        updatedAt: serverTimestamp()
      });

      const partnerProfileUpdateRef = doc(db, 'profiles', partnerUserId);
      await updateDoc(partnerProfileUpdateRef, {
        partnerId: currentUser.uid,
        coupleId: coupleId,
        updatedAt: serverTimestamp()
      });

      const coupleRef = doc(db, 'couples', coupleId);
      const coupleExists = await getDoc(coupleRef);
      
      if (!coupleExists.exists()) {
        await setDoc(coupleRef, {
          id: coupleId,
          user1_id: currentUser.uid,
          user2_id: partnerUserId,
          created_at: serverTimestamp(),
          trust_meter: 0.5,
          vulnerability_meter: 0.5,
          romance_meter: 0.5,
          connection_meter: 0.5,
          total_points: 0,
          streak_days: 0,
          last_interaction: serverTimestamp()
        });
      } else {
        await updateDoc(coupleRef, {
          last_interaction: serverTimestamp()
        });
      }

      Alert.alert(
        'Success!', 
        'You are now linked with your partner!', 
        [
          { text: 'Continue', onPress: () => navigation.navigate('DashboardHome' as never) }
        ]
      );
    } catch (error) {
      console.error('Error linking couple:', error);
      Alert.alert('Error', 'Failed to link with partner. Please try again.');
    }
  };

  return (
    <ScreenLayout>
      <RadialGradientBackground />
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <Typography variant="header" style={styles.mainTitle}>Link Your Cosmic Connection</Typography>
          <Typography variant="body" style={styles.subtitle}>Enter your partner's cosmic code to sync your journey.</Typography>

          <GlassCard style={styles.glassPanel}>
            <Typography variant="label" style={styles.inputLabel}>Partner's Cosmic Code</Typography>
            <TextInput
              style={styles.input}
              placeholder="XXXX-XXXX"
              placeholderTextColor={COLORS.textHint}
              value={partnerCode}
              onChangeText={setPartnerCode}
              autoCapitalize="characters"
              maxLength={9}
            />

            <SquishyButton onPress={handleLinkCouple}>
              <Typography variant="button">Link Cosmic Connection</Typography>
            </SquishyButton>

            <SquishyButton 
              variant="secondary"
              onPress={() => navigation.navigate('OnboardingCurrentVibe' as never)}
            >
              <Typography variant="button">Generate My Code</Typography>
            </SquishyButton>
          </GlassCard>
        </ScrollView>
      </KeyboardAvoidingView>
    </ScreenLayout>
  );
};

const styles = StyleSheet.create({
  keyboardView: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.screenPadding,
  },
  mainTitle: {
    textAlign: 'center',
    marginBottom: SPACING.small,
    paddingHorizontal: SPACING.regular,
  },
  subtitle: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SPACING.xxlarge,
  },
  glassPanel: {
    width: '100%',
    maxWidth: 400,
    borderRadius: BORDER_RADIUS.xlarge,
    padding: SPACING.xlarge,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    overflow: 'hidden',
    backgroundColor: COLORS.backgroundPrimary + '99',
  },
  inputLabel: {
    marginBottom: SPACING.small,
  },
  input: {
    height: 48,
    backgroundColor: COLORS.backgroundInput,
    borderRadius: BORDER_RADIUS.input,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    paddingHorizontal: SPACING.regular,
    color: COLORS.textPrimary,
    fontSize: TYPOGRAPHY.fontSize.bodyLarge,
    marginBottom: SPACING.large,
    textAlign: 'center',
  },
});

export default CoupleLinkingScreen;
