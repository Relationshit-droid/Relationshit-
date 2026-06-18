
import type { FirebaseApp } from 'firebase/app';

async function getAiAnalysisCallable() {
  const { getFunctions, httpsCallable } = await import('firebase/functions');
  const { app } = await import('./firebaseClient');
  const functions = getFunctions(app as FirebaseApp);
  return httpsCallable(functions, 'getAiAnalysis');
}

/**
 * Gets AI analysis by calling the secure Firebase Function.
 * @param promptText The text prompt to be analyzed.
 * @returns A promise that resolves with an object containing the AI's analysis.
 * @throws Throws an error if the cloud function call fails.
 */
export const getSecureAiAnalysis = async (promptText: string): Promise<{ analysis: string }> => {
  try {
    console.log("Calling getAiAnalysis Cloud Function...");

    const getAiAnalysis = await getAiAnalysisCallable();
    const result = await getAiAnalysis({ promptText });
    
    // The result data is automatically typed from your cloud function's return type.
    const data = result.data as { analysis: string };

    console.log("Received analysis from Cloud Function.");
    return data;

  } catch (error) {
    console.error("Firebase function call failed", error);
    // The error object from Firebase is detailed. You can inspect it for specific codes.
    // For the user, we'll throw a generic message.
    throw new Error("Failed to get analysis. Please check your connection and try again.");
  }
};

// Example of how to use it in your components:
/*
import { getSecureAiAnalysis } from './lib/ai-engine';

const MyComponent = () => {
  const [analysis, setAnalysis] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePress = async () => {
    setIsLoading(true);
    try {
      const result = await getSecureAiAnalysis("My partner seems distant.");
      setAnalysis(result.analysis);
    } catch (error) {
      console.error(error);
      // Show an error message to the user
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View>
      <Button title="Get Analysis" onPress={handlePress} />
      {isLoading ? <ActivityIndicator /> : <Text>{analysis}</Text>}
    </View>
  );
};
*/
