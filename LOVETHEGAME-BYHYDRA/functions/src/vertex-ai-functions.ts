import * as functions from 'firebase-functions';
import { VertexAI, FunctionDeclarationSchemaType, HarmCategory, HarmBlockThreshold } from '@google-cloud/vertexai';
import { getStorage } from 'firebase-admin/storage';
import { TextToSpeechClient } from '@google-cloud/text-to-speech';

// Initialize Vertex AI
const vertexAI = new VertexAI({
  project: process.env.GCLOUD_PROJECT || 'love-actually-game',
  location: 'us-central1',
});

// --- Gemini Model Configuration ---
const MODEL_CONFIG = {
  temperature: 0.8, 
  topP: 0.8,
  topK: 40,
  maxOutputTokens: 2048,
};

const SAFETY_SETTINGS = [
    { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
    { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
    { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
    { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
];

// --- Tool and Function Declarations for Gemini --- 

const analysisFunction = {
    name: 'perform_analysis',
    description: 'Performs a detailed analysis of user input within a relationship context.',
    parameters: {
        type: FunctionDeclarationSchemaType.OBJECT,
        properties: {
            sentiment: { type: FunctionDeclarationSchemaType.STRING, description: 'Sentiment of the user input (e.g., positive, negative, neutral, vulnerable).' },
            confidence: { type: FunctionDeclarationSchemaType.NUMBER, description: 'Confidence score (0.0-1.0) of the sentiment analysis.' },
            triggers: { type: FunctionDeclarationSchemaType.STRING, description: 'Comma-separated list of emotional triggers detected in the input.' },
            marcieResponse: { type: FunctionDeclarationSchemaType.STRING, description: 'Dr. Marcie\'s empathetic, witty response to the user input.' },
            intensity: { type: FunctionDeclarationSchemaType.INTEGER, description: 'Emotional intensity of the input on a scale of 1-10.' },
            relationshipImpact: { type: FunctionDeclarationSchemaType.STRING, description: 'A brief insight into the potential significance of the input on the couple\'s relationship.' },
        },
        required: ['sentiment', 'confidence', 'triggers', 'marcieResponse', 'intensity', 'relationshipImpact']
    }
};

const tools = [{ function_declarations: [analysisFunction] }];


// Initialize the generative model with tools
const generativeModel = vertexAI.getGenerativeModel({
  model: 'gemini-1.0-pro-001',
  generation_config: MODEL_CONFIG,
  safety_settings: SAFETY_SETTINGS,
  tools: tools,
});

const ttsClient = new TextToSpeechClient();


// --- Firebase Cloud Functions --- 

/**
 * Generates personalized game content using Gemini and a detailed prompt.
 */
export const generateGameContent = functions.runWith({ memory: '256MB', timeoutSeconds: 60 }).https.onCall(async (data, context) => {
    if (!context.auth) throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');

    const { gameType, prompt } = data;
    if (!gameType || !prompt) throw new functions.https.HttpsError('invalid-argument', 'Missing required parameters');

    // Detailed system prompts (no change from original)
    const systemPrompt = `...`; // Your existing system prompts here

    try {
        const result = await generativeModel.generateContent({ contents: [{ role: 'user', parts: [{ text: systemPrompt }] }] });
        const response = result.response;
        const text = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
        
        let content = {};
        try {
            const jsonMatch = text.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                content = JSON.parse(jsonMatch[0]);
            } else {
                content = { commentary: text };
            }
        } catch (e) {
            console.error("Failed to parse AI response:", e, "Raw text:", text);
            content = { commentary: text, error: 'Failed to parse structured response' };
        }
        
        await logAIGeneration(gameType, context.auth.uid, prompt, text);
        return { content };

    } catch (error) {
        console.error('Vertex AI generation error:', error);
        throw new functions.https.HttpsError('internal', 'AI content generation failed', { fallback: getFallbackContent(gameType) });
    }
});

/**
 * Analyzes user input for emotional content using Gemini Function Calling.
 */
export const analyzeUserInput = functions.runWith({ memory: '256MB', timeoutSeconds: 30 }).https.onCall(async (data, context) => {
    if (!context.auth) throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated.');
    
    const { input, context: analysisContext } = data;
    if (!input) throw new functions.https.HttpsError('invalid-argument', 'Input text is required.');

    const prompt = `Analyze this user input for emotional content and relationship significance:\n\"${input}\"\n\nContext: ${JSON.stringify(analysisContext)}\n\nNow, use the provided tool to perform the analysis.`;

    try {
        const result = await generativeModel.generateContent({ contents: [{ role: 'user', parts: [{ text: prompt }] }] });
        const response = result.response;
        const functionCall = response.candidates?.[0]?.content?.parts.find(p => p.functionCall)?.functionCall;

        if (functionCall && functionCall.args) {
            const analysis = functionCall.args; // Arguments are already parsed JSON
            return { success: true, analysis };
        } else {
             // Fallback if the model doesn\'t call the function
            return { success: false, analysis: { marcieResponse: "I'm not sure how to respond to that, darling. Can you tell me more?" } };
        }

    } catch (error) {
        console.error('Input analysis error:', error);
        throw new functions.https.HttpsError('internal', 'Failed to analyze input.');
    }
});

/**
 * Synthesizes speech for Marcie's responses using Google Cloud Text-to-Speech 
 * and serves it securely from Firebase Storage.
 */
export const synthesizeSpeech = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated.');
  }

  const { text, voiceSettings } = data;
  if (!text) {
    throw new functions.https.HttpsError('invalid-argument', 'Text to synthesize is required.');
  }
  
  const storage = getStorage();
  const bucket = storage.bucket(process.env.GCLOUD_STORAGE_BUCKET || `${process.env.GCLOUD_PROJECT}.appspot.com`);

  const voiceName = voiceSettings?.voiceId || 'en-US-Wavenet-F'; // Default voice
  const speakingRate = voiceSettings?.speed || 1.1;
  const pitch = voiceSettings?.pitch || -2.0;

  // Generate a unique filename
  const fileName = `marcie-audio/${context.auth.uid}/${Date.now()}.mp3`;
  const file = bucket.file(fileName);

  try {
    const [response] = await ttsClient.synthesizeSpeech({
      input: { text },
      voice: { languageCode: 'en-US', name: voiceName },
      audioConfig: { audioEncoding: 'MP3', speakingRate, pitch },
    });

    if (!response.audioContent) {
      throw new Error('No audio content received from TTS API.');
    }

    // Save the audio to Firebase Storage
    await file.save(Buffer.from(response.audioContent), { resumable: false });

    // Get a signed URL for the client to access the file
    const [signedUrl] = await file.getSignedUrl({
      action: 'read',
      expires: Date.now() + 15 * 60 * 1000, // 15 minutes
    });

    const duration = (text.split(' ').length / speakingRate) * 500; // Estimated duration

    return {
      audioUrl: signedUrl,
      duration: Math.round(duration),
      text: text,
    };

  } catch (error) {
    console.error('Speech synthesis error:', error);
    throw new functions.https.HttpsError('internal', 'Failed to synthesize speech. Please try again later.');
  }
});

// --- Helper Functions (unchanged) ---
async function logAIGeneration(gameType: string, userId: string, prompt: string, response: string): Promise<void> {
  /* ... */
}

function getFallbackContent(gameType: string): any {
  /* ... */
}
