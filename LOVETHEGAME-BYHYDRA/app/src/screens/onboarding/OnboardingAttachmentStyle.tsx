import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { ScreenLayout } from '../../layout';
import { Typography, GlassCard, SquishyButton, RadialGradientBackground } from '../../components/ui';
import { COLORS, GRADIENTS, SPACING, BORDER_RADIUS, SHADOWS } from '../../theme';
import { Ionicons } from '@expo/vector-icons';

const AttachmentStyleOption = ({ title, subtitle, color, icon, onPress }: any) => (
  <SquishyButton style={[styles.optionButton, { borderColor: color }]} onPress={onPress}>
    <View style={[styles.iconContainer, { backgroundColor: color + '33' }]}>
      <Ionicons name={icon} size={24} color={color} />
    </View>
    <View style={styles.optionTextContainer}>
      <Typography variant="body" style={{ color }}>{title}</Typography>
      <Typography variant="caption" style={{ color: COLORS.textSecondary }}>{subtitle}</Typography>
    </View>
  </SquishyButton>
);

const OnboardingAttachmentStyleScreen = () => {
  return (
    <ScreenLayout>
      <RadialGradientBackground />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.progressContainer}>
          <Typography variant="caption" style={styles.stepText}>Step 5 of 8</Typography>
          <Typography variant="label" style={styles.questionCounter}>Question 9 / 10</Typography>
        </View>
        <View style={styles.progressBar}>
          <View style={[styles.progressBarFill, { width: '90%' }]} />
        </View>

        <GlassCard style={styles.quizContainer}>
          <Typography variant="header" style={styles.questionText}>When you feel insecure in a relationship, what is your first instinct?</Typography>
          <Typography variant="caption" style={styles.questionSubtitle}>Select the response that feels most natural to you</Typography>

          <View style={styles.optionsGrid}>
            <AttachmentStyleOption 
              title="Communicate Openly" 
              subtitle="I talk about my feelings calmly" 
              color={COLORS.mintGreen} 
              icon="chatbubbles"
            />
            <AttachmentStyleOption 
              title="Seek Reassurance" 
              subtitle="I need constant signs of love" 
              color={COLORS.brightYellow} 
              icon="heart"
            />
            <AttachmentStyleOption 
              title="Create Distance" 
              subtitle="I withdraw to protect myself" 
              color={COLORS.rosePink} 
              icon="shield"
            />
            <AttachmentStyleOption 
              title="Fluctuating Reactions" 
              subtitle="My reaction varies unpredictably" 
              color={COLORS.lavenderPurple} 
              icon="sync"
            />
          </View>
        </GlassCard>

        <View style={styles.navContainer}>
          <SquishyButton variant="ghost">
            <Typography variant="label" style={styles.navButton}>PREVIOUS</Typography>
          </SquishyButton>
          <SquishyButton>
            <Typography variant="button">NEXT QUESTION</Typography>
          </SquishyButton>
        </View>
      </ScrollView>
    </ScreenLayout>
  );
};

const styles = StyleSheet.create({
  scrollContent: { 
    padding: SPACING.screenPadding, 
    justifyContent: 'space-between', 
    flexGrow: 1 
  },
  progressContainer: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: SPACING.small 
  },
  stepText: { 
    color: COLORS.textSecondary 
  },
  questionCounter: { 
    color: COLORS.vibrantPink 
  },
  progressBar: { 
    height: 6, 
    backgroundColor: COLORS.textPrimary + '0D', 
    borderRadius: BORDER_RADIUS.small, 
    marginBottom: SPACING.xlarge 
  },
  progressBarFill: { 
    height: '100%', 
    backgroundColor: COLORS.vibrantPink, 
    borderRadius: BORDER_RADIUS.small 
  },
  quizContainer: { 
    padding: SPACING.xlarge 
  },
  questionText: { 
    textAlign: 'center', 
    marginBottom: SPACING.small 
  },
  questionSubtitle: { 
    textAlign: 'center', 
    marginBottom: SPACING.xxlarge,
    color: COLORS.textSecondary,
  },
  optionsGrid: { 
    gap: SPACING.regular 
  },
  optionButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: COLORS.backgroundInput, 
    padding: SPACING.regular, 
    borderRadius: BORDER_RADIUS.large, 
    borderWidth: 1, 
    borderColor: COLORS.borderSubtle 
  },
  iconContainer: { 
    width: 48, 
    height: 48, 
    borderRadius: BORDER_RADIUS.medium, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginRight: SPACING.regular 
  },
  optionTextContainer: { 
    flex: 1 
  },
  navContainer: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginTop: SPACING.xlarge 
  },
  navButton: { 
    color: COLORS.textSecondary 
  },
});

export default OnboardingAttachmentStyleScreen;
