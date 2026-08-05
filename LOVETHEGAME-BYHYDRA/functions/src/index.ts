import * as admin from "firebase-admin";
import { onCall, HttpsError } from "firebase-functions/v2/https";
import { generateGameContent, analyzeUserInput, synthesizeSpeech } from './vertex-ai-functions';

admin.initializeApp();

// Export Vertex AI functions
export { generateGameContent, analyzeUserInput, synthesizeSpeech };

export const calculateGameResults = onCall(async (request) => {
  if (!request.auth) {
    throw new HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }
  const { gameId, user1Answers, user2Answers, partnerId } = request.data;
  const db = admin.firestore();

  // Basic scoring logic - this should be expanded based on game type
  let score = 0;
  for (let i = 0; i < user1Answers.length; i++) {
    if (user1Answers[i] === user2Answers[i]) {
      score += 10;
    }
  }

  const gameRef = db.collection("games").doc(gameId);
  await gameRef.update({ score });

  // Update the trust thermometer
  const uid = request.auth.uid;
  const user1Ref = db.collection("users").doc(uid);
  const user2Ref = db.collection("users").doc(partnerId); // Assuming partnerId is passed in

  await db.runTransaction(async (transaction) => {
    const user1Doc = await transaction.get(user1Ref);
    const user2Doc = await transaction.get(user2Ref);

    if (!user1Doc.exists || !user2Doc.exists) {
      throw new Error("User not found");
    }

    const user1Data = user1Doc.data();
    const user2Data = user2Doc.data();

    if (!user1Data || !user2Data) {
        throw new Error("User data not found");
    }

    const user1Trust = user1Data.trust_thermometer || 50;
    const user2Trust = user2Data.trust_thermometer || 50;

    const newTrust = (user1Trust + user2Trust + score) / 3;

    transaction.update(user1Ref, { trust_thermometer: newTrust });
    transaction.update(user2Ref, { trust_thermometer: newTrust });
  });

  return { score };
});
