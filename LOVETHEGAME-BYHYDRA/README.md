# Love Actually - The Game

A couples therapy app disguised as a game, hosted by Dr. Marcie Liss - a brutally honest AI therapist with charm, wit, and zero tolerance for BS.

## 🎮 Overview

This app transforms couples therapy into an engaging game experience with:
- 7 different game categories focused on relationship building
- The Love Arcade - championship matches of honesty and emotional parkour
- Dr. Marcie Liss AI therapist with 4 levels of "sarcasm therapy"
- Real-time couple synchronization
- SOS Fight Solver for conflict resolution

## 🛠 Tech Stack

- **Frontend**: React Native Expo (TypeScript)
- **Backend**: FastAPI (Python)
- **Database**: Firebase Firestore
- **AI**: Google Gemini (1.5 Flash/Pro) for relationship coaching and therapy simulation.
- **UI**: Tailwind CSS with NativeWind

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Expo CLI installed globally

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd LOVETRAE
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment variables**

Create `.env` file in the `app` directory:
```bash
EXPO_PUBLIC_API_URL=http://localhost:8001
EXPO_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
EXPO_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
EXPO_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef

# AI API Keys (optional for local development)
EXPO_PUBLIC_OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```

4. **Run the development servers**

Start both backend and frontend:
```bash
npm run dev
```

Or run separately:
```bash
# Terminal 1: Start backend
npm run dev:backend

# Terminal 2: Start frontend
npm run dev:app
```

## 🏗️ Architecture

### Backend API Endpoints
- `/api/users` - User management
- `/api/couples/link` - Couple linking
- `/api/games/categories` - Game categories
- `/api/love-arcade/games` - Love Arcade games
- `/api/marcie/chat` - Dr. Marcie AI interactions
- `/api/sos/sessions` - SOS conflict resolution

### Real-time Features
- WebSocket connections for couple synchronization
- Firebase Firestore for persistent data
- Live presence detection

## 🎯 Game Categories

1. **Emotional Connection** - SEEN Method focused games
2. **Conflict Resolution** - Gottman-inspired healing
3. **Creative Chaos** - Playful creative challenges
4. **Romance Hub** - Spicy & sweet connections
5. **Healing Hospital** - Deep repair & recovery
6. **Game Show** - Classic formats
7. **The Love Arcade** - Championship matches (featured)

## 🤖 Dr. Marcie AI System

4 Sarcasm Levels:
1. **Tough Love Rookie** - Mild sarcasm, warm but blunt
2. **Reality Check Specialist** - Clinical, analytical sarcasm
3. **Radical Truth Wizard** - Deep, powerful, poetic truth
4. **The Glamour Oracle** - Full Noir Prophecy Mode

## 📱 Deployment

### Backend (Render)
1. Create a Render account
2. Create a new Web Service
3. Connect to this GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Add environment variables as needed

### Frontend (Expo)
```bash
cd app
expo publish
```

Or build for specific platforms:
```bash
expo build:android
expo build:ios
```

## 🧪 Testing

Run backend tests:
```bash
npm run test:backend
```

## 🔧 Troubleshooting

### Common Issues

1. **Backend not connecting to frontend**
   - Ensure both are running on the correct ports
   - Check your `.env` file has the correct `EXPO_PUBLIC_API_URL`

2. **Firebase authentication not working**
   - Verify your Firebase project configuration
   - Ensure environment variables are properly set

3. **Dr. Marcie AI not responding**
   - Check that your LLM API keys are properly configured
   - Verify network connectivity to the AI provider

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please contact the development team or open an issue in the repository.

---

Made with ❤️ for couples everywhere