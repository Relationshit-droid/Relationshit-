import { Audio } from 'expo-av';
import { synthesize } from './elevenlabs';

export async function speakMarcie(text: string) {
  try {
    const file = await synthesize(text);
    const sound = new Audio.Sound();
    await sound.loadAsync({ uri: file });
    await sound.playAsync();
  } catch (e: any) {
    try {
      const w: any = typeof window !== 'undefined' ? window : null;
      if (w && w.speechSynthesis && w.SpeechSynthesisUtterance) {
        const u = new w.SpeechSynthesisUtterance(text);
        w.speechSynthesis.cancel();
        w.speechSynthesis.speak(u);
      }
    } catch {}
  }
}
