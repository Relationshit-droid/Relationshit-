"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.calculateGameResults = exports.synthesizeSpeech = exports.analyzeUserInput = exports.generateGameContent = void 0;
const admin = require("firebase-admin");
const https_1 = require("firebase-functions/v2/https");
const vertex_ai_functions_1 = require("./vertex-ai-functions");
Object.defineProperty(exports, "generateGameContent", { enumerable: true, get: function () { return vertex_ai_functions_1.generateGameContent; } });
Object.defineProperty(exports, "analyzeUserInput", { enumerable: true, get: function () { return vertex_ai_functions_1.analyzeUserInput; } });
Object.defineProperty(exports, "synthesizeSpeech", { enumerable: true, get: function () { return vertex_ai_functions_1.synthesizeSpeech; } });
admin.initializeApp();
exports.calculateGameResults = (0, https_1.onCall)(async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError('unauthenticated', 'The function must be called while authenticated.');
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
//# sourceMappingURL=index.js.map