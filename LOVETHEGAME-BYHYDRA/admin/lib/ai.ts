
import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as logger from "firebase-functions/logger";
import * as admin from 'firebase-admin';
import { OpenAI } from "openai";

// Initialize Firebase Admin SDK if not already initialized
if (admin.apps.length === 0) {
  admin.initializeApp();
}

// The OpenAI API key is sourced from the environment variable `OPENAI_API_KEY`
// This secret needs to be set up in Firebase Secret Manager.
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const getAiAnalysis = onCall(
  // The 'secrets' option makes the secret value available as an environment variable
  { secrets: ["OPENAI_API_KEY"] },
  async (request) => {
    // 1. Authentication Check
    if (!request.auth) {
      logger.error("Unauthenticated user tried to call getAiAnalysis");
      throw new HttpsError("unauthenticated", "You must be logged in to use this feature.");
    }

    // 2. Input Validation
    const promptText = request.data.promptText;
    if (typeof promptText !== 'string' || promptText.length === 0) {
      logger.warn("getAiAnalysis called with invalid promptText", { uid: request.auth.uid });
      throw new HttpsError("invalid-argument", "The function must be called with a non-empty 'promptText' string.");
    }

    // 3. API Call Logic
    const fullPrompt = `You are Dr. Marcie Liss, a witty and brutally honest couples therapist. Analyze the following user statement: ${promptText}`;

    try {
      logger.info(`Calling OpenAI for user: ${request.auth.uid}`);
      // The OpenAI library handles making the POST request to the Chat Completions endpoint
      // and includes the Authorization header.
      const completion = await openai.chat.completions.create({
        messages: [{ role: "user", content: fullPrompt }],
        model: "gpt-3.5-turbo",
      });

      const analysis = completion.choices[0]?.message?.content;

      if (!analysis) {
          logger.error("OpenAI response was empty or in an unexpected format.", { uid: request.auth.uid });
          throw new HttpsError('internal', 'Failed to get analysis. Please try again later.');
      }

      logger.info(`Successfully received analysis for user: ${request.auth.uid}`);
      // 4. Output
      return { analysis };

    } catch (error) {
      // 5. Error Handling
      logger.error("Error calling OpenAI API:", { error, uid: request.auth.uid });
      throw new HttpsError("internal", "Failed to get analysis. Please try again later.");
    }
  }
);
