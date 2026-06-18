import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ScrollView,
  ActivityIndicator,
  Animated as RNAnimated,
  Easing,
  Image,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { auth } from '../../lib/firebaseClient';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { Typography, SquishyButton } from '../../components/ui';
import { ScreenLayout } from '../../layout';
import { userApi } from '../../lib/api';
import { COLORS, GRADIENTS, TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS, ANIMATIONS } from '../../theme';

const LoginAndSignUpScreen = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigation = useNavigation();

  const logoScale = useRef(new RNAnimated.Value(0.8)).current;
  const logoGlow = useRef(new RNAnimated.Value(0.5)).current;
  const fadeIn = useRef(new RNAnimated.Value(0)).current;
  const slideUp = useRef(new RNAnimated.Value(50)).current;

  useEffect(() => {
    RNAnimated.spring(logoScale, {
      toValue: 1,
      friction: 8,
      tension: 40,
      useNativeDriver: true,
    }).start();

    RNAnimated.loop(
      RNAnimated.sequence([
        RNAnimated.timing(logoGlow, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        RNAnimated.timing(logoGlow, {
          toValue: 0.5,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    ).start();

    RNAnimated.timing(fadeIn, {
      toValue: 1,
      duration: ANIMATIONS.duration.slow,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();

    RNAnimated.timing(slideUp, {
      toValue: 0,
      duration: ANIMATIONS.duration.slow,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, []);

  const handleAuth = async () => {
    setIsLoading(true);
    
    try {
      if (isLogin) {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken();
        console.log('User logged in, token obtained');
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        const token = await user.getIdToken();
        console.log('Firebase user created, token obtained');
        
        try {
          const displayName = email.split('@')[0];
          await userApi.create(
            {
              email: user.email || email,
              display_name: displayName
            },
            token
          );
          console.log('Backend user created successfully');
          await updateProfile(user, { displayName });
        } catch (backendError) {
          console.error('Backend user creation failed:', backendError);
          Alert.alert(
            'Account Created',
            'Your account was created successfully. Some features may be limited until sync completes.',
            [{ text: 'OK' }]
          );
        }
      }
    } catch (error: any) {
      console.error('Authentication error:', error);
      Alert.alert(
        'Authentication Failed',
        error.message || 'An error occurred during authentication'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScreenLayout showHeader={false} scrollable={false}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContainer}
          keyboardShouldPersistTaps="handled"
        >
          <RNAnimated.View
            style={[
              styles.logoContainer,
              {
                transform: [{ scale: logoScale }],
                opacity: logoGlow,
              },
            ]}
          >
            <View style={styles.logoGlow}>
              <Image
                source={require('../../assets/logo/mainlogoone.png')}
                style={styles.logo}
                resizeMode="contain"
              />
            </View>
          </RNAnimated.View>

          <RNAnimated.View
            style={[
              styles.titleContainer,
              { opacity: fadeIn, transform: [{ translateY: slideUp }] },
            ]}
          >
            <Typography variant="gameTitle" style={styles.mainTitle}>
              Navigate the stars of your relationship.
            </Typography>
            
            {!isLogin && (
              <Typography variant="marcieDialogue" style={styles.tagline}>
                "How about we DON'T Break Up?"
              </Typography>
            )}
            
            <Typography variant="body" style={styles.subtitle}>
              Sync your frequencies to begin the journey.
            </Typography>
          </RNAnimated.View>

          <RNAnimated.View
            style={[
              styles.panelContainer,
              { opacity: fadeIn, transform: [{ translateY: slideUp }] },
            ]}
          >
            <BlurView intensity={20} tint="dark" style={styles.glassPanel}>
              <View style={styles.toggleContainer}>
                <SquishyButton
                  onPress={() => setIsLogin(true)}
                  variant={isLogin ? 'primary' : 'secondary'}
                  style={styles.toggleButton}
                >
                  <Typography variant="button">LOGIN</Typography>
                </SquishyButton>
                <SquishyButton
                  onPress={() => setIsLogin(false)}
                  variant={!isLogin ? 'primary' : 'secondary'}
                  style={styles.toggleButton}
                >
                  <Typography variant="button">SIGN UP</Typography>
                </SquishyButton>
              </View>

              <Typography variant="label" style={styles.inputLabel}>YOUR COSMIC HANDLE</Typography>
              <View style={styles.inputWrapper}>
                <LinearGradient
                  colors={GRADIENTS.primary.colors}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.gradientBorder}
                >
                  <View style={styles.inputContainer}>
                    <TextInput
                      style={styles.input}
                      placeholder="commander@nebula.space"
                      placeholderTextColor={COLORS.textHint}
                      value={email}
                      onChangeText={setEmail}
                      keyboardType="email-address"
                      autoCapitalize="none"
                      autoComplete="email"
                    />
                  </View>
                </LinearGradient>
              </View>

              <Typography variant="label" style={styles.inputLabel}>SECRET FREQUENCY</Typography>
              <View style={styles.inputWrapper}>
                <LinearGradient
                  colors={GRADIENTS.primary.colors}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.gradientBorder}
                >
                  <View style={styles.inputContainer}>
                    <TextInput
                      style={styles.input}
                      placeholder="••••••••••••"
                      placeholderTextColor={COLORS.textHint}
                      value={password}
                      onChangeText={setPassword}
                      secureTextEntry
                      autoComplete="password"
                    />
                  </View>
                </LinearGradient>
              </View>

              <SquishyButton 
                onPress={handleAuth}
                disabled={isLoading}
                style={styles.authButton}
              >
                {isLoading ? (
                  <ActivityIndicator color={COLORS.textPrimary} />
                ) : (
                  <Typography variant="button">
                    {isLogin ? 'INITIATE CONNECTION' : 'CREATE ACCOUNT'}
                  </Typography>
                )}
              </SquishyButton>
            </BlurView>
          </RNAnimated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </ScreenLayout>
  );
};

import { RadialGradientBackground } from '../../components/ui';

const styles = StyleSheet.create({
  keyboardView: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.screenPadding,
    paddingTop: Platform.OS === 'ios' ? SPACING.xxxlarge : SPACING.xxlarge,
    paddingBottom: SPACING.xxlarge,
  },
  logoContainer: {
    marginBottom: SPACING.xxlarge,
    alignItems: 'center',
  },
  logoGlow: {
    ...SHADOWS.neonStrong,
  },
  logo: {
    width: 120,
    height: 120,
  },
  titleContainer: {
    alignItems: 'center',
    marginBottom: SPACING.xxlarge,
    paddingHorizontal: SPACING.large,
  },
  mainTitle: {
    textAlign: 'center',
  },
  tagline: {
    color: COLORS.vibrantPink,
    textAlign: 'center',
    marginTop: SPACING.medium,
    opacity: 0.9,
  },
  subtitle: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: SPACING.small,
  },
  panelContainer: {
    width: '100%',
    maxWidth: 400,
  },
  glassPanel: {
    borderRadius: BORDER_RADIUS.xlarge,
    padding: SPACING.xlarge,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    overflow: 'hidden',
    backgroundColor: COLORS.backgroundModal,
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: BORDER_RADIUS.xlarge,
    padding: SPACING.tiny,
    marginBottom: SPACING.xlarge,
  },
  toggleButton: {
    flex: 1,
  },
  inputLabel: {
    marginBottom: SPACING.small,
  },
  inputWrapper: {
    marginBottom: SPACING.large,
  },
  gradientBorder: {
    borderRadius: BORDER_RADIUS.xlarge,
    padding: 2,
  },
  inputContainer: {
    backgroundColor: COLORS.backgroundModal,
    borderRadius: BORDER_RADIUS.xlarge - 2,
    overflow: 'hidden',
  },
  input: {
    height: 52,
    paddingHorizontal: SPACING.regular,
    color: COLORS.textPrimary,
    fontFamily: TYPOGRAPHY.fontFamily.regular,
    fontSize: TYPOGRAPHY.fontSize.bodyLarge,
  },
  authButton: {
    marginTop: SPACING.large,
  },
});

export default LoginAndSignUpScreen;
