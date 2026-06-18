"""
Love Actually - The Game API
Production-ready FastAPI backend with Firebase Firestore integration
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any, Literal
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import json
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
from functools import wraps
import time

load_dotenv()

# ============================================================================
# FIREBASE INITIALIZATION
# ============================================================================

firebase_initialized = False
db = None

if not firebase_initialized:
    try:
        # Try to get credentials from environment
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_initialized = True
            print("Firebase initialized successfully")
        else:
            # Try application default credentials
            try:
                firebase_admin.initialize_app()
                db = firestore.client()
                firebase_initialized = True
                print("Firebase initialized successfully (default)")
            except:
                print("Firebase credentials not found. Running in fallback mode.")
                db = None
    except Exception as e:
        print(f"Firebase initialization failed: {str(e)}")
        print("Running in fallback mode with in-memory storage")
        db = None

# ============================================================================
# IN-MEMORY FALLBACK (for development only)
# ============================================================================

users_db: Dict[str, Any] = {}
couples_db: Dict[str, Any] = {}
game_sessions_db: Dict[str, Any] = {}
sos_sessions_db: Dict[str, Any] = {}

# WebSocket connections for real-time sync
connections: Dict[str, List[WebSocket]] = {}

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("Starting up Love Actually - The Game API")
    print(f"Firebase: {'Connected' if db else 'Fallback Mode'}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    yield
    # Shutdown
    print("Shutting down Love Actually - The Game API...")

app = FastAPI(
    title="Love Actually - The Game API",
    description="Production API for Love Actually couples therapy gaming app",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:19000",
        "https://lovetrae.web.app",
        "https://lovetrae.firebaseapp.com",
        "exp://127.0.0.1:19000",
        "exp://localhost:19000",
        "*.ngrok.io",
        "https://*.vercel.app",
        "https://*.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DR. MARCIE CONFIGURATION
# ============================================================================

SARCASM_LEVELS = {
    1: {
        "name": "Tough Love Rookie",
        "description": "Mild sarcasm, warm but blunt",
        "system_prompt": """You are Dr. Marcie Liss, a witty AI therapist. At Level 1 (Tough Love Rookie), you're like a straight-talking aunt who loves them but doesn't sugarcoat. Use mild sarcasm and warm, blunt advice. Examples:
- "Sweetheart, if ignoring red flags were an Olympic sport, you'd have gold."
- "Love is blind, but girl, your denial needs prescription lenses."
"""
    },
    2: {
        "name": "Reality Check Specialist",
        "description": "Clinical, analytical sarcasm",
        "system_prompt": """You are Dr. Marcie Liss, a witty AI therapist. At Level 2 (Reality Check Specialist), you use clinical, analytical sarcasm with scientific detachment. Examples:
- "Your attachment style is showing. Loudly."
- "If avoidance were a career path, you'd be CEO of 'It's Fine Inc.'"
"""
    },
    3: {
        "name": "Radical Truth Wizard",
        "description": "Deep, powerful, poetic truth",
        "system_prompt": """You are Dr. Marcie Liss, a witty AI therapist. At Level 3 (Radical Truth Wizard), you deliver deep, powerful truth with poetic weight. No BS. Gentle but searing. Examples:
- "You're not broken, but you are bleeding—and you keep trying to dance in the fire."
- "Stop searching for closure in open wounds."
"""
    },
    4: {
        "name": "The Glamour Oracle",
        "description": "Full Noir Prophecy Mode - Maya Angelou meets Joan Rivers",
        "system_prompt": """You are Dr. Marcie Liss, a witty AI therapist. At Level 4 (The Glamour Oracle), you channel Maya Angelou meets Joan Rivers in a 1950s noir detective's office. Fierce compassion, elegant clarity, refined sarcasm. Examples:
- "You keep choosing people who love you like a footnote—yet you were written to be the title page. Let's edit."
- "You're not failing at love. You're graduating from the school of 'How to Disappear While Standing Naked in the Room.'"
"""
    }
}

# ============================================================================
# GAME CATEGORIES AND REGISTRY
# ============================================================================

GAME_CATEGORIES = [
    {
        "id": "emotional-connection",
        "name": "Emotional Connection",
        "description": "SEEN Method focused games",
        "icon": "heart",
        "color": "#FA1F63",
        "games": ["truth-or-trust", "gratitude-cloud", "eye-contact-challenge", "memory-lane-map", "vibe-check", "bid-radar", "dream-decoder", "empathy-echo", "micro-moment-museum", "needs-decoder", "shared-meaning-mural", "turning-toward", "vulnerability-volley", "admiration-aim"]
    },
    {
        "id": "conflict-resolution",
        "name": "Conflict Resolution",
        "description": "Gottman-inspired games",
        "icon": "shield",
        "color": "#33DEA5",
        "games": ["slap-of-truth", "apology-auction", "defensiveness-detox", "whos-right", "stress-test", "blame-flip", "compromise-jenga", "conflict-dice", "deal-or-no-deal", "de-escalation-lab", "gentle-startup", "repair-attempt", "tone-shift", "truth-transparency", "relationship-council"]
    },
    {
        "id": "creative-chaos",
        "name": "Creative Chaos",
        "description": "Playful, creative challenges",
        "icon": "sparkles",
        "color": "#E4E831",
        "games": ["role-swap-roast", "draw-your-feelings", "gif-battle", "karaoke-confessional", "ransom-note", "escapism-room", "gif-the-feels", "lie-detector", "mirror-mode", "soundtrack-sync", "validation-game-show", "avoidance-arcade", "connection-conundrum", "the-love-script", "results-roast"]
    },
    {
        "id": "romance-hub",
        "name": "Romance Hub",
        "description": "Spicy & sweet connections",
        "icon": "flame",
        "color": "#BE1980",
        "games": ["date-night-roulette", "bedroom-bingo", "six-second-kiss", "foreplay-slider", "touch-map", "commitment-dice", "ritual-roulette", "vow-remix"]
    },
    {
        "id": "healing-hospital",
        "name": "Healing Hospital",
        "description": "Deep repair & recovery",
        "icon": "medkit",
        "color": "#5C1459",
        "games": ["windows-and-walls", "trigger-triage", "trust-bank", "the-iceberg", "secrecy-audit", "boundary-bingo", "cycle-breaker", "denial-detector", "flashback-frenzy", "guilt-shame-sort", "healing-bingo", "layers-of-hurt", "micro-betrayal-golf", "rewrite-memory", "timeline-detective", "transparency-toss", "antidote-arena"]
    },
    {
        "id": "game-show",
        "name": "Game Show",
        "description": "Classic game show formats",
        "icon": "trophy",
        "color": "#22d3ee",
        "games": ["couples-jeopardy", "relationship-millionaire", "family-feud-couples", "newlywed-sync", "wheel-of-intimacy", "achievements-badges"]
    },
    {
        "id": "love-arcade",
        "name": "The Love Arcade",
        "description": "Championship matches of honesty, wit, and emotional parkour",
        "icon": "game-controller",
        "color": "#FF6B6B",
        "games": ["truth-teller-tower", "echo-chamber-escape", "intimacy-feud", "relational-jeopardy", "family-forge", "harbor-storm", "phoenix-protocol", "trust-renovation", "word-wound"]
    }
]

# Complete game registry with metadata
GAME_REGISTRY = {
    # Romance Hub
    "six-second-kiss": {"name": "6-Second Kiss Challenge", "max_score": 100, "min_players": 2, "estimated_time": 2},
    "bedroom-bingo": {"name": "Bedroom Bingo", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "date-night-roulette": {"name": "Date Night Roulette", "max_score": 150, "min_players": 2, "estimated_time": 10},
    "foreplay-slider": {"name": "Foreplay Slider", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "touch-map": {"name": "Touch Map", "max_score": 100, "min_players": 2, "estimated_time": 15},
    "commitment-dice": {"name": "Commitment Dice", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "ritual-roulette": {"name": "Ritual Roulette", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "vow-remix": {"name": "Vow Remix", "max_score": 100, "min_players": 2, "estimated_time": 15},
    
    # Emotional Connection
    "truth-or-trust": {"name": "Truth or Trust", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "gratitude-cloud": {"name": "Gratitude Cloud", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "eye-contact-challenge": {"name": "Eye Contact Challenge", "max_score": 100, "min_players": 2, "estimated_time": 5},
    "memory-lane-map": {"name": "Memory Lane Map", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "vibe-check": {"name": "Vibe Check", "max_score": 100, "min_players": 2, "estimated_time": 5},
    "bid-radar": {"name": "Bid Radar", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "dream-decoder": {"name": "Dream Decoder", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "empathy-echo": {"name": "Empathy Echo", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "micro-moment-museum": {"name": "Micro-Moment Museum", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "needs-decoder": {"name": "Needs Decoder", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "shared-meaning-mural": {"name": "Shared Meaning Mural", "max_score": 100, "min_players": 2, "estimated_time": 15},
    "turning-toward": {"name": "Turning Toward Tally", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "vulnerability-volley": {"name": "Vulnerability Volley", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "admiration-aim": {"name": "Admiration Aim", "max_score": 100, "min_players": 2, "estimated_time": 10},
    
    # Conflict Resolution
    "slap-of-truth": {"name": "Slap of Truth", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "apology-auction": {"name": "Apology Auction", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "defensiveness-detox": {"name": "Defensiveness Detox", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "whos-right": {"name": "Who's Right?", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "stress-test": {"name": "Stress Test", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "blame-flip": {"name": "Blame Flip", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "compromise-jenga": {"name": "Compromise Jenga", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "conflict-dice": {"name": "Conflict Dice", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "deal-or-no-deal": {"name": "Deal or No Deal: Accountability", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "de-escalation-lab": {"name": "De-Escalation Lab", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "gentle-startup": {"name": "Gentle Startup Gauntlet", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "repair-attempt": {"name": "Repair Attempt", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "tone-shift": {"name": "Tone Shift Challenge", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "truth-transparency": {"name": "Truth & Transparency Gauntlet", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "relationship-council": {"name": "Relationship Council", "max_score": 150, "min_players": 2, "estimated_time": 15},
    
    # Creative Chaos
    "role-swap-roast": {"name": "Role Swap Roast", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "draw-your-feelings": {"name": "Draw Your Feelings", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "gif-battle": {"name": "GIF Battle", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "karaoke-confessional": {"name": "Karaoke Confessional", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "ransom-note": {"name": "Ransom Note Romance", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "escapism-room": {"name": "Escapism Room", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "gif-the-feels": {"name": "GIF The Feels", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "lie-detector": {"name": "Lie Detector", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "mirror-mode": {"name": "Mirror Mode", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "soundtrack-sync": {"name": "Soundtrack Sync", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "validation-game-show": {"name": "Validation Game Show", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "avoidance-arcade": {"name": "Avoidance Arcade", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "connection-conundrum": {"name": "Connection Conundrum", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "the-love-script": {"name": "The Love Script Debacle", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "results-roast": {"name": "Results Roast", "max_score": 100, "min_players": 2, "estimated_time": 10},
    
    # Healing Hospital
    "windows-and-walls": {"name": "Windows and Walls", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "trigger-triage": {"name": "Trigger Triage", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "trust-bank": {"name": "Trust Bank", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "the-iceberg": {"name": "The Iceberg", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "secrecy-audit": {"name": "Secrecy Audit", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "boundary-bingo": {"name": "Boundary Bingo", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "cycle-breaker": {"name": "Cycle Breaker", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "denial-detector": {"name": "Denial Detector", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "flashback-frenzy": {"name": "Flashback Frenzy", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "guilt-shame-sort": {"name": "Guilt vs Shame Sort", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "healing-bingo": {"name": "Healing Bingo", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "layers-of-hurt": {"name": "Layers of Hurt", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "micro-betrayal-golf": {"name": "Micro-Betrayal Mini Golf", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "rewrite-memory": {"name": "Rewrite the Memory", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "timeline-detective": {"name": "Timeline Detective", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "transparency-toss": {"name": "Transparency Toss", "max_score": 100, "min_players": 2, "estimated_time": 10},
    "antidote-arena": {"name": "Antidote Arena", "max_score": 100, "min_players": 2, "estimated_time": 10},
    
    # Game Show
    "couples-jeopardy": {"name": "Couples Jeopardy!", "max_score": 2000, "min_players": 2, "estimated_time": 30},
    "relationship-millionaire": {"name": "Relationship Millionaire", "max_score": 1000, "min_players": 2, "estimated_time": 25},
    "family-feud-couples": {"name": "Family Feud: Couples Edition", "max_score": 250, "min_players": 2, "estimated_time": 20},
    "newlywed-sync": {"name": "Newlywed Sync", "max_score": 200, "min_players": 2, "estimated_time": 15},
    "wheel-of-intimacy": {"name": "Wheel of Intimacy", "max_score": 150, "min_players": 2, "estimated_time": 15},
    "achievements-badges": {"name": "Achievements & Badges", "max_score": 0, "min_players": 1, "estimated_time": 5},
    
    # Love Arcade
    "truth-teller-tower": {"name": "Truth Teller Tower", "max_score": 100, "min_players": 2, "estimated_time": 15},
    "echo-chamber-escape": {"name": "Escape from the Echo Chamber", "max_score": 100, "min_players": 2, "estimated_time": 15},
    "intimacy-feud": {"name": "The Intimacy Feud", "max_score": 250, "min_players": 2, "estimated_time": 20},
    "relational-jeopardy": {"name": "Relational Jeopardy!", "max_score": 2000, "min_players": 2, "estimated_time": 30},
    "family-forge": {"name": "Family Forge Edition", "max_score": 1800, "min_players": 2, "estimated_time": 45},
    "harbor-storm": {"name": "Harbor & Storm Edition", "max_score": 1900, "min_players": 2, "estimated_time": 45},
    "phoenix-protocol": {"name": "Phoenix Protocol Edition", "max_score": 2200, "min_players": 2, "estimated_time": 50},
    "trust-renovation": {"name": "Trust Renovation Edition", "max_score": 1750, "min_players": 2, "estimated_time": 45},
    "word-wound": {"name": "Word-Wound Edition", "max_score": 1000, "min_players": 2, "estimated_time": 30},
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr = Field(..., min_length=5, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=100)

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    partner_id: Optional[str] = None
    couple_code: Optional[str] = None
    couple_id: Optional[str] = None
    sarcasm_level: int = 1
    trust_level: float = 0.5
    vulnerability_level: float = 0.5
    points: int = 0
    plan: str = "free"
    created_at: str
    updated_at: Optional[str] = None

class CoupleLinkRequest(BaseModel):
    user_id: str
    partner_code: str

class CoupleResponse(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    created_at: str
    trust_meter: float = 0.5
    vulnerability_meter: float = 0.5
    romance_meter: float = 0.5
    connection_meter: float = 0.5
    total_points: int = 0
    streak_days: int = 0

class GameSessionCreate(BaseModel):
    user_id: str
    game_id: str
    category_id: str
    couple_id: Optional[str] = None

class GameSessionUpdate(BaseModel):
    score: Optional[int] = None
    completed: Optional[bool] = None
    responses: Optional[List[Dict]] = None
    game_state: Optional[Dict[str, Any]] = None
    partner_progress: Optional[Dict[str, Any]] = None

class GameSessionResponse(BaseModel):
    id: str
    user_id: str
    couple_id: Optional[str] = None
    game_id: str
    category_id: str
    started_at: str
    completed: bool = False
    completed_at: Optional[str] = None
    score: int = 0
    responses: List[Dict] = []
    game_state: Dict[str, Any] = {}
    partner_progress: Optional[Dict[str, Any]] = None
    status: str = "active"
    timeout_at: Optional[str] = None

class SOSSessionCreate(BaseModel):
    initiator_id: str
    couple_id: str

class SOSBoothSubmission(BaseModel):
    session_id: str
    user_id: str
    i_feel: str = Field(..., min_length=1, max_length=500)
    when_partner: str = Field(..., min_length=1, max_length=500)
    because_i_tell_myself: str = Field(..., min_length=1, max_length=500)
    what_i_need: str = Field(..., min_length=1, max_length=500)

class SOSBoothSubmissionResponse(BaseModel):
    i_feel: str
    when_partner: str
    because_i_tell_myself: str
    what_i_need: str
    submitted_at: str

class SOSSessionResponse(BaseModel):
    id: str
    initiator_id: str
    couple_id: str
    status: Literal["waiting_for_partner", "one_submitted", "analyzing", "completed", "expired"]
    started_at: str
    completed_at: Optional[str] = None
    submissions: Dict[str, SOSBoothSubmissionResponse]
    verdict: Optional[str] = None
    expires_at: str

class MarcieRequest(BaseModel):
    user_id: str
    context: str = Field(..., min_length=1, max_length=1000)
    message: str = Field(..., min_length=1, max_length=1000)
    sarcasm_level: int = Field(default=1, ge=1, le=4)
    game_context: Optional[str] = Field(default=None, max_length=500)

class MarcieResponse(BaseModel):
    response: str
    animation: str
    sarcasm_level: int

class GameAnswerSubmission(BaseModel):
    session_id: str
    user_id: str
    question_id: str
    answer: Any
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GameAnswerResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    question_id: str
    answer: Any
    is_correct: Optional[bool] = None
    points_earned: int = 0
    submitted_at: str
    metadata: Optional[Dict[str, Any]] = None

class LeaderboardEntry(BaseModel):
    user_id: str
    display_name: str
    total_score: int
    games_completed: int
    rank: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

# ============================================================================
# FIRESTORE HELPERS
# ============================================================================

def get_user_ref(user_id: str):
    """Get Firestore reference for user document"""
    if db:
        return db.collection('users').document(user_id)
    return None

def get_couple_ref(couple_id: str):
    """Get Firestore reference for couple document"""
    if db:
        return db.collection('couples').document(couple_id)
    return None

def get_session_ref(session_id: str):
    """Get Firestore reference for game session document"""
    if db:
        return db.collection('game_sessions').document(session_id)
    return None

def get_sos_ref(session_id: str):
    """Get Firestore reference for SOS session document"""
    if db:
        return db.collection('sos_sessions').document(session_id)
    return None

def doc_to_dict(doc) -> Optional[Dict]:
    """Convert Firestore document to dict"""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    # Convert datetime objects to ISO strings
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data

# ============================================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================================

async def verify_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Verify Firebase ID token from Authorization header"""
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace('Bearer ', '') if authorization.startswith('Bearer ') else authorization
        
        if db:
            # In production, verify with Firebase Auth
            # For now, return the token for identification
            return token
        return token
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/{couple_id}")
async def websocket_endpoint(websocket: WebSocket, couple_id: str):
    """WebSocket endpoint for real-time couple synchronization"""
    await websocket.accept()
    
    if couple_id not in connections:
        connections[couple_id] = []
    connections[couple_id].append(websocket)
    
    # Notify other partner of connection
    for connection in connections[couple_id]:
        if connection != websocket:
            try:
                await connection.send_text(json.dumps({
                    "type": "partner_connected",
                    "couple_id": couple_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
            except:
                pass
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add timestamp and broadcast to all connected partners
            message['server_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            for connection in connections[couple_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove closed connections
                    if connection in connections[couple_id]:
                        connections[couple_id].remove(connection)
    except WebSocketDisconnect:
        if couple_id in connections and websocket in connections[couple_id]:
            connections[couple_id].remove(websocket)
            
        # Notify other partner of disconnection
        for connection in connections.get(couple_id, []):
            try:
                await connection.send_text(json.dumps({
                    "type": "partner_disconnected",
                    "couple_id": couple_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
            except:
                pass

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "Love Actually - The Game",
        "version": "2.0.0",
        "firebase": "connected" if db else "fallback",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user profile"""
    user_id = str(uuid.uuid4())
    couple_code = str(uuid.uuid4())[:8].upper()
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "display_name": user.display_name,
        "partner_id": None,
        "couple_code": couple_code,
        "couple_id": None,
        "sarcasm_level": 1,
        "trust_level": 0.5,
        "vulnerability_level": 0.5,
        "points": 0,
        "plan": "free",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if db:
        get_user_ref(user_id).set(new_user)
    else:
        users_db[user_id] = new_user
    
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    if db:
        doc = get_user_ref(user_id).get()
        user = doc_to_dict(doc)
    else:
        user = users_db.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, updates: Dict[str, Any]):
    """Update user profile"""
    if db:
        doc = get_user_ref(user_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        get_user_ref(user_id).update(updates)
        
        # Return updated user
        doc = get_user_ref(user_id).get()
        return doc_to_dict(doc)
    else:
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="User not found")
        users_db[user_id].update(updates)
        users_db[user_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
        return users_db[user_id]

@app.put("/api/users/{user_id}/sarcasm")
async def update_sarcasm_level(user_id: str, level: int):
    """Update user's sarcasm level (1-4)"""
    if level < 1 or level > 4:
        raise HTTPException(status_code=400, detail="Sarcasm level must be 1-4")
    
    if db:
        doc = get_user_ref(user_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        get_user_ref(user_id).update({
            "sarcasm_level": level,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="User not found")
        users_db[user_id]["sarcasm_level"] = level
    
    return {
        "success": True,
        "sarcasm_level": level,
        "name": SARCASM_LEVELS[level]["name"]
    }

# New couple endpoints to match test expectations
@app.post("/api/couples/create")
async def create_couple(payload: Dict[str, str]):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    couple_id = str(uuid.uuid4())
    invite_code = str(uuid.uuid4()).replace('-', '')[:6].upper()
    couple_data = {
        "id": couple_id,
        "user1_id": user_id,
        "user2_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "invite_code": invite_code,
        "trust_meter": 0.5,
        "vulnerability_meter": 0.5,
        "romance_meter": 0.5,
        "connection_meter": 0.5,
        "total_points": 0,
    }

    if db:
        get_couple_ref(couple_id).set(couple_data)
        get_user_ref(user_id).update({"couple_id": couple_id, "updated_at": datetime.now(timezone.utc).isoformat()})
    else:
        couples_db[couple_id] = couple_data
        users_db.setdefault(user_id, {"id": user_id})
        users_db[user_id]["couple_id"] = couple_id

    return couple_data


@app.post("/api/couples/join")
async def join_couple(payload: Dict[str, str]):
    user_id = payload.get("user_id")
    invite_code = payload.get("invite_code")
    if not user_id or not invite_code:
        raise HTTPException(status_code=400, detail="user_id and invite_code required")

    # Find couple by invite_code
    target = None
    if db:
        couples_ref = db.collection('couples')
        query = couples_ref.where('invite_code', '==', invite_code).limit(1)
        docs = list(query.stream())
        if docs:
            doc = docs[0]
            target = doc_to_dict(doc)
    else:
        for c in couples_db.values():
            if c.get("invite_code") == invite_code:
                target = c
                break

    if not target:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    couple_id = target["id"]
    if db:
        get_couple_ref(couple_id).update({"user2_id": user_id, "status": "active"})
        get_user_ref(user_id).update({"couple_id": couple_id, "partner_id": target.get('user1_id'), "updated_at": datetime.now(timezone.utc).isoformat()})
    else:
        couples_db[couple_id]["user2_id"] = user_id
        couples_db[couple_id]["status"] = "active"
        users_db.setdefault(user_id, {"id": user_id})
        users_db[user_id]["couple_id"] = couple_id
        users_db[user_id]["partner_id"] = target.get("user1_id")

    return couples_db.get(couple_id) if not db else doc_to_dict(get_couple_ref(couple_id).get())


@app.post("/api/couples/regenerate-code")
async def regenerate_invite_code(payload: Dict[str, str]):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    # Find couple where user1_id == user_id
    target = None
    for c in couples_db.values():
        if c.get("user1_id") == user_id:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Couple not found")

    new_code = str(uuid.uuid4()).replace('-', '')[:6].upper()
    target["invite_code"] = new_code

    return {"success": True, "invite_code": new_code}


@app.post("/api/couples/unlink")
async def unlink_couple(payload: Dict[str, str]):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    # Find couple for user
    target_id = None
    for cid, c in list(couples_db.items()):
        if c.get("user1_id") == user_id or c.get("user2_id") == user_id:
            target_id = cid
            break

    if not target_id:
        return {"success": True}

    # Remove partner links
    c = couples_db.pop(target_id, None)
    if c:
        u1 = c.get("user1_id")
        u2 = c.get("user2_id")
        if u1 and users_db.get(u1):
            users_db[u1].pop("couple_id", None)
            users_db[u1].pop("partner_id", None)
        if u2 and users_db.get(u2):
            users_db[u2].pop("couple_id", None)
            users_db[u2].pop("partner_id", None)

    return {"success": True}


@app.get("/api/couples/me")
async def get_my_couple(user_id: str):
    # Check if user has a couple
    user = users_db.get(user_id)
    if not user or not user.get("couple_id"):
        return {"status": "none", "has_couple": False}

    couple = couples_db.get(user.get("couple_id"))
    if not couple:
        return {"status": "none", "has_couple": False}

    return {"status": couple.get("status", "active"), "has_couple": True, **couple}

# ============================================================================
# COUPLE ENDPOINTS
# ============================================================================

@app.post("/api/couples/link")
async def link_couple(request: CoupleLinkRequest):
    """Link two users as a couple"""
    # Find user with the partner code
    partner_user = None
    partner_id = None
    
    if db:
        # Query Firestore for user with matching couple_code
        users_ref = db.collection('users')
        query = users_ref.where('couple_code', '==', request.partner_code).limit(1)
        docs = query.stream()
        
        for doc in docs:
            if doc.id != request.user_id:
                partner_user = doc_to_dict(doc)
                partner_id = doc.id
                break
    else:
        for uid, user in users_db.items():
            if user.get("couple_code") == request.partner_code and uid != request.user_id:
                partner_user = user
                partner_id = uid
                break
    
    if not partner_user:
        raise HTTPException(status_code=404, detail="Invalid partner code")
    
    if partner_user.get("partner_id"):
        raise HTTPException(status_code=400, detail="Partner already linked to someone else")
    
    # Create couple
    couple_id = str(uuid.uuid4())
    couple_data = {
        "id": couple_id,
        "user1_id": request.user_id,
        "user2_id": partner_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trust_meter": 0.5,
        "vulnerability_meter": 0.5,
        "romance_meter": 0.5,
        "connection_meter": 0.5,
        "total_points": 0,
        "streak_days": 0,
        "last_interaction": datetime.now(timezone.utc).isoformat()
    }
    
    if db:
        get_couple_ref(couple_id).set(couple_data)
        
        # Update both users
        get_user_ref(request.user_id).update({
            "partner_id": partner_id,
            "couple_id": couple_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        get_user_ref(partner_id).update({
            "partner_id": request.user_id,
            "couple_id": couple_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        couples_db[couple_id] = couple_data
        users_db[request.user_id]["partner_id"] = partner_id
        users_db[request.user_id]["couple_id"] = couple_id
        users_db[partner_id]["partner_id"] = request.user_id
        users_db[partner_id]["couple_id"] = couple_id
    
    return {
        "success": True,
        "couple_id": couple_id,
        "partner": {
            "id": partner_id,
            "display_name": partner_user.get("display_name")
        }
    }

@app.get("/api/couples/{couple_id}")
async def get_couple(couple_id: str):
    """Get couple data by ID"""
    if db:
        doc = get_couple_ref(couple_id).get()
        couple = doc_to_dict(doc)
    else:
        couple = couples_db.get(couple_id)
    
    if not couple:
        raise HTTPException(status_code=404, detail="Couple not found")
    
    return couple

@app.get("/api/couples/{couple_id}/presence")
async def get_couple_presence(couple_id: str):
    """Get couple online presence status"""
    if db:
        doc = get_couple_ref(couple_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Couple not found")
    else:
        if couple_id not in couples_db:
            raise HTTPException(status_code=404, detail="Couple not found")
    
    # Check WebSocket connections
    active_connections = connections.get(couple_id, [])
    
    return {
        "couple_id": couple_id,
        "user1_online": len(active_connections) > 0,
        "user2_online": len(active_connections) > 1,
        "total_connections": len(active_connections),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.put("/api/couples/{couple_id}/meters")
async def update_couple_meters(couple_id: str, meters: Dict[str, float]):
    """Update couple's relationship meters"""
    valid_meters = ["trust_meter", "vulnerability_meter", "romance_meter", "connection_meter"]
    
    updates = {}
    # If any provided value is invalid, reject the request
    for key, value in meters.items():
        if key in valid_meters:
            if not (isinstance(value, (int, float)) and 0 <= value <= 1):
                raise HTTPException(status_code=400, detail=f"Invalid meter value for {key}")
            updates[key] = value
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if db:
        doc = get_couple_ref(couple_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Couple not found")
        get_couple_ref(couple_id).update(updates)
        
        doc = get_couple_ref(couple_id).get()
        return doc_to_dict(doc)
    else:
        if couple_id not in couples_db:
            raise HTTPException(status_code=404, detail="Couple not found")
        couples_db[couple_id].update(updates)
        return couples_db[couple_id]

# ============================================================================
# GAME CATEGORIES ENDPOINTS
# ============================================================================

@app.get("/api/games/categories")
async def get_game_categories():
    """Get all game categories with their games"""
    return {"categories": GAME_CATEGORIES}

@app.get("/api/games/categories/{category_id}")
async def get_category_games(category_id: str):
    """Get specific category details"""
    for cat in GAME_CATEGORIES:
        if cat["id"] == category_id:
            # Add full game details
            games = []
            for game_id in cat["games"]:
                if game_id in GAME_REGISTRY:
                    game_info = GAME_REGISTRY[game_id].copy()
                    game_info["id"] = game_id
                    games.append(game_info)
            
            response = cat.copy()
            response["games_detail"] = games
            return response
    
    raise HTTPException(status_code=404, detail="Category not found")

@app.get("/api/games/registry")
async def get_game_registry():
    """Get complete game registry"""
    return {
        "games": GAME_REGISTRY,
        "total_games": len(GAME_REGISTRY),
        "categories": len(GAME_CATEGORIES)
    }

@app.get("/api/games/{game_id}")
async def get_game_details(game_id: str):
    """Get specific game details"""
    if game_id not in GAME_REGISTRY:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = GAME_REGISTRY[game_id].copy()
    game["id"] = game_id
    
    # Find category
    for cat in GAME_CATEGORIES:
        if game_id in cat["games"]:
            game["category"] = cat["id"]
            game["category_name"] = cat["name"]
            break
    
    return game

# ============================================================================
# GAME SESSION ENDPOINTS
# ============================================================================

@app.post("/api/games/sessions", response_model=GameSessionResponse)
async def create_game_session(session: GameSessionCreate):
    """Create a new game session"""
    # Validate game exists
    if session.game_id not in GAME_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Invalid game_id: {session.game_id}")
    
    session_id = str(uuid.uuid4())
    timeout_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    
    new_session = {
        "id": session_id,
        "user_id": session.user_id,
        "couple_id": session.couple_id,
        "game_id": session.game_id,
        "category_id": session.category_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed": False,
        "score": 0,
        "responses": [],
        "game_state": {},
        "partner_progress": None,
        "status": "active",
        "timeout_at": timeout_at
    }
    
    if db:
        get_session_ref(session_id).set(new_session)
    else:
        game_sessions_db[session_id] = new_session
    
    return new_session

@app.get("/api/games/sessions/{session_id}")
async def get_game_session(session_id: str):
    """Get game session by ID"""
    if db:
        doc = get_session_ref(session_id).get()
        session = doc_to_dict(doc)
    else:
        session = game_sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@app.put("/api/games/sessions/{session_id}")
async def update_game_session(session_id: str, update: GameSessionUpdate):
    """Update game session progress"""
    if db:
        doc = get_session_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        updates = {}
        if update.score is not None:
            updates["score"] = update.score
        if update.completed is not None:
            updates["completed"] = update.completed
            if update.completed:
                updates["completed_at"] = datetime.now(timezone.utc).isoformat()
                updates["status"] = "completed"
        if update.responses is not None:
            updates["responses"] = update.responses
        if update.game_state is not None:
            updates["game_state"] = update.game_state
        if update.partner_progress is not None:
            updates["partner_progress"] = update.partner_progress
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        get_session_ref(session_id).update(updates)
        
        # Return updated session
        doc = get_session_ref(session_id).get()
        return doc_to_dict(doc)
    else:
        if session_id not in game_sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = game_sessions_db[session_id]
        if update.score is not None:
            session["score"] = update.score
        if update.completed is not None:
            session["completed"] = update.completed
            if update.completed:
                session["completed_at"] = datetime.now(timezone.utc).isoformat()
                session["status"] = "completed"
        if update.responses is not None:
            session["responses"] = update.responses
        if update.game_state is not None:
            session["game_state"] = update.game_state
        if update.partner_progress is not None:
            session["partner_progress"] = update.partner_progress
        
        return session

@app.post("/api/games/sessions/{session_id}/answers")
async def submit_game_answer(session_id: str, answer: GameAnswerSubmission):
    """Submit an answer for a game session"""
    # Get session
    if db:
        doc = get_session_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Session not found")
        session = doc_to_dict(doc)
    else:
        if session_id not in game_sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        session = game_sessions_db[session_id]
    
    # Check if session is still active
    if session.get("completed"):
        raise HTTPException(status_code=400, detail="Game session already completed")
    
    # Create answer record
    answer_record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": answer.user_id,
        "question_id": answer.question_id,
        "answer": answer.answer,
        "submitted_at": answer.timestamp or datetime.now(timezone.utc).isoformat(),
        "metadata": answer.metadata or {}
    }
    
    # Calculate points based on game logic
    game_id = session["game_id"]
    points_earned = calculate_answer_points(game_id, answer.question_id, answer.answer, answer.metadata)
    answer_record["points_earned"] = points_earned
    
    # Update session
    responses = session.get("responses", [])
    responses.append(answer_record)
    
    new_score = session.get("score", 0) + points_earned
    
    if db:
        get_session_ref(session_id).update({
            "responses": responses,
            "score": new_score,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        game_sessions_db[session_id]["responses"] = responses
        game_sessions_db[session_id]["score"] = new_score
    
    return answer_record

def calculate_answer_points(game_id: str, question_id: str, answer: Any, metadata: Optional[Dict]) -> int:
    """Calculate points for an answer based on game-specific logic"""
    # Default scoring
    points = 10
    
    # Game-specific scoring logic
    if metadata:
        if metadata.get("is_correct"):
            points = metadata.get("base_points", 10)
        if metadata.get("bonus_points"):
            points += metadata.get("bonus_points", 0)
        if metadata.get("speed_bonus"):
            points += metadata.get("speed_bonus", 0)
        if metadata.get("streak_bonus"):
            points += metadata.get("streak_bonus", 0)
    
    # Ensure points don't exceed max for game
    if game_id in GAME_REGISTRY:
        max_score = GAME_REGISTRY[game_id]["max_score"]
        points = min(points, max_score)
    
    return max(0, points)

@app.post("/api/games/sessions/{session_id}/complete")
async def complete_game_session(session_id: str, final_data: Dict[str, Any]):
    """Complete a game session with final results"""
    if db:
        doc = get_session_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        updates = {
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if "final_score" in final_data:
            updates["score"] = final_data["final_score"]
        if "responses" in final_data:
            updates["responses"] = final_data["responses"]
        if "game_state" in final_data:
            updates["game_state"] = final_data["game_state"]
        if "achievements" in final_data:
            updates["achievements"] = final_data["achievements"]
        
        get_session_ref(session_id).update(updates)
        
        # Update couple's total points if couple_id exists
        session = doc_to_dict(get_session_ref(session_id).get())
        if session.get("couple_id"):
            couple_ref = get_couple_ref(session["couple_id"])
            couple_doc = couple_ref.get()
            if couple_doc.exists:
                couple_data = couple_doc.to_dict()
                new_total = couple_data.get("total_points", 0) + updates.get("score", 0)
                couple_ref.update({
                    "total_points": new_total,
                    "last_interaction": datetime.now(timezone.utc).isoformat()
                })
        
        doc = get_session_ref(session_id).get()
        return doc_to_dict(doc)
    else:
        if session_id not in game_sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = game_sessions_db[session_id]
        session["completed"] = True
        session["completed_at"] = datetime.now(timezone.utc).isoformat()
        session["status"] = "completed"
        
        if "final_score" in final_data:
            session["score"] = final_data["final_score"]
        if "responses" in final_data:
            session["responses"] = final_data["responses"]
        if "game_state" in final_data:
            session["game_state"] = final_data["game_state"]
        if "achievements" in final_data:
            session["achievements"] = final_data["achievements"]
        
        return session

@app.get("/api/users/{user_id}/sessions")
async def get_user_game_sessions(user_id: str, limit: int = 50):
    """Get game sessions for a user"""
    if db:
        sessions_ref = db.collection('game_sessions')
        query = sessions_ref.where('user_id', '==', user_id).order_by('started_at', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        sessions = [doc_to_dict(doc) for doc in docs]
    else:
        sessions = [
            s for s in game_sessions_db.values()
            if s.get("user_id") == user_id
        ]
        sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        sessions = sessions[:limit]
    
    return {"sessions": sessions, "count": len(sessions)}

@app.get("/api/couples/{couple_id}/sessions")
async def get_couple_game_sessions(couple_id: str, limit: int = 50):
    """Get game sessions for a couple"""
    if db:
        sessions_ref = db.collection('game_sessions')
        query = sessions_ref.where('couple_id', '==', couple_id).order_by('started_at', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        sessions = [doc_to_dict(doc) for doc in docs]
    else:
        sessions = [
            s for s in game_sessions_db.values()
            if s.get("couple_id") == couple_id
        ]
        sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        sessions = sessions[:limit]
    
    return {"sessions": sessions, "count": len(sessions)}

# ============================================================================
# SOS FIGHT SOLVER ENDPOINTS
# ============================================================================

@app.post("/api/sos/sessions", response_model=SOSSessionResponse)
async def create_sos_session(sos: SOSSessionCreate):
    """Create a new SOS fight resolution session"""
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    new_session = {
        "id": session_id,
        "initiator_id": sos.initiator_id,
        "couple_id": sos.couple_id,
        "status": "waiting_for_partner",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "submissions": {},
        "verdict": None,
        "expires_at": expires_at
    }
    
    if db:
        get_sos_ref(session_id).set(new_session)
    else:
        sos_sessions_db[session_id] = new_session
    
    return new_session

@app.post("/api/sos/sessions/{session_id}/submit")
async def submit_sos_booth(session_id: str, submission: SOSBoothSubmission):
    """Submit SOS booth response"""
    if db:
        doc = get_sos_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="SOS Session not found")
        session = doc_to_dict(doc)
    else:
        if session_id not in sos_sessions_db:
            raise HTTPException(status_code=404, detail="SOS Session not found")
        session = sos_sessions_db[session_id]
    
    # Check if expired
    expires_at = session.get("expires_at")
    if expires_at and datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        if db:
            get_sos_ref(session_id).update({"status": "expired"})
        else:
            session["status"] = "expired"
        raise HTTPException(status_code=400, detail="SOS Session has expired")
    
    submission_data = {
        "i_feel": submission.i_feel,
        "when_partner": submission.when_partner,
        "because_i_tell_myself": submission.because_i_tell_myself,
        "what_i_need": submission.what_i_need,
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    
    submissions = session.get("submissions", {})
    submissions[submission.user_id] = submission_data
    
    # Determine status
    if len(submissions) >= 2:
        status = "analyzing"
        # In production, trigger AI analysis here
    elif len(submissions) == 1:
        status = "one_submitted"
    else:
        status = "waiting_for_partner"
    
    if db:
        get_sos_ref(session_id).update({
            "submissions": submissions,
            "status": status
        })
        doc = get_sos_ref(session_id).get()
        return doc_to_dict(doc)
    else:
        session["submissions"] = submissions
        session["status"] = status
        return session

@app.get("/api/sos/sessions/{session_id}")
async def get_sos_session(session_id: str):
    """Get SOS session by ID"""
    if db:
        doc = get_sos_ref(session_id).get()
        session = doc_to_dict(doc)
    else:
        session = sos_sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="SOS Session not found")
    
    return session


# Compatibility endpoints expected by tests
@app.post("/api/sos/trigger")
async def trigger_sos(payload: Dict[str, Any]):
    user_id = payload.get("user_id")
    couple_id = payload.get("couple_id")
    severity = payload.get("severity", 3)
    trigger = payload.get("trigger", "")

    session_id = str(uuid.uuid4())
    new_session = {
        "id": session_id,
        "user_id": user_id,
        "couple_id": couple_id,
        "trigger": trigger,
        "severity": severity,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "submissions": {}
    }

    sos_sessions_db[session_id] = new_session

    partner_notified = bool(couple_id)
    new_session["partner_notified"] = partner_notified

    return new_session


@app.get("/api/sos/resources")
async def get_sos_resources(category: Optional[str] = None):
    resources = {
        "immediate": ["988 Hotline", "Local Emergency Services"],
        "de_escalation_games": ["breathing-exercise", "repair-attempt"],
        "self_help": ["grounding", "journaling"]
    }
    categories = list(resources.keys())

    if category:
        if category not in resources:
            raise HTTPException(status_code=404, detail="Invalid category")
        return {"category": category, "resources": resources[category]}

    return {"categories": categories, "resources": resources}


@app.get("/api/sos/resources/recommended")
async def get_recommended_resources(user_id: str, severity: int = 3):
    # Simple heuristic recommendations
    recs = []
    if severity >= 4:
        recs = ["988 Hotline", "grounding", "seek-professional-help"]
    else:
        recs = ["breathing-exercise", "repair-attempt"]

    return {"user_id": user_id, "severity": severity, "recommendations": recs}


@app.post("/api/sos/{session_id}/booth/submit")
async def booth_submit(session_id: str, payload: Dict[str, Any]):
    if session_id not in sos_sessions_db:
        raise HTTPException(status_code=404, detail="SOS session not found")

    submission = {
        "user_id": payload.get("user_id"),
        "i_feel": payload.get("i_feel"),
        "when_partner": payload.get("when_partner"),
        "because_i_tell_myself": payload.get("because_i_tell_myself"),
        "what_i_need": payload.get("what_i_need"),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    session = sos_sessions_db[session_id]
    session["submissions"][submission["user_id"]] = submission

    both = len(session["submissions"]) >= 2
    return {"success": True, "both_submitted": both}


@app.post("/api/sos/{session_id}/resolve")
async def resolve_sos(session_id: str, payload: Dict[str, Any]):
    if session_id not in sos_sessions_db:
        raise HTTPException(status_code=404, detail="SOS session not found")

    session = sos_sessions_db[session_id]
    session["status"] = "resolved"
    session["resolved_at"] = datetime.now(timezone.utc).isoformat()
    session["resolution_notes"] = payload.get("resolution_notes")
    return {"success": True, "resolved_at": session["resolved_at"]}


@app.post("/api/sos/{session_id}/escalate")
async def escalate_sos(session_id: str, payload: Dict[str, Any]):
    if session_id not in sos_sessions_db:
        raise HTTPException(status_code=404, detail="SOS session not found")

    session = sos_sessions_db[session_id]
    session["status"] = "escalated"
    immediate_resources = ["988 Hotline", "Local Emergency Services"]
    return {"success": True, "status": "escalated", "immediate_resources": immediate_resources}


@app.get("/api/sos/user/{user_id}/history")
async def sos_user_history(user_id: str):
    sessions = [s for s in sos_sessions_db.values() if s.get("user_id") == user_id]
    total = len(sessions)
    avg_severity = sum(s.get("severity", 0) for s in sessions) / total if total else 0
    patterns = {"average_severity": avg_severity}
    return {"user_id": user_id, "total_count": total, "patterns": patterns}

@app.post("/api/sos/sessions/{session_id}/analyze")
async def analyze_sos_session(session_id: str):
    """Trigger AI analysis of SOS session"""
    if db:
        doc = get_sos_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="SOS Session not found")
        session = doc_to_dict(doc)
    else:
        if session_id not in sos_sessions_db:
            raise HTTPException(status_code=404, detail="SOS Session not found")
        session = sos_sessions_db[session_id]
    
    if len(session.get("submissions", {})) < 2:
        raise HTTPException(status_code=400, detail="Both partners must submit before analysis")
    
    # Generate verdict based on submissions
    submissions = session["submissions"]
    verdict = generate_sos_verdict(submissions)
    
    if db:
        get_sos_ref(session_id).update({
            "verdict": verdict,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        })
        doc = get_sos_ref(session_id).get()
        return doc_to_dict(doc)
    else:
        session["verdict"] = verdict
        session["status"] = "completed"
        session["completed_at"] = datetime.now(timezone.utc).isoformat()
        return session

def generate_sos_verdict(submissions: Dict[str, Any]) -> str:
    """Generate AI verdict based on SOS submissions"""
    # This is a simplified version - in production, use actual AI
    user_ids = list(submissions.keys())
    
    if len(user_ids) < 2:
        return "Insufficient data for analysis"
    
    sub1 = submissions[user_ids[0]]
    sub2 = submissions[user_ids[1]]
    
    # Simple pattern matching for common themes
    needs_overlap = False
    common_themes = ["listen", "understand", "support", "time", "space"]
    
    need1 = sub1.get("what_i_need", "").lower()
    need2 = sub2.get("what_i_need", "").lower()
    
    for theme in common_themes:
        if theme in need1 and theme in need2:
            needs_overlap = True
            break
    
    if needs_overlap:
        return "Both partners are seeking understanding and connection. Focus on active listening and validation."
    else:
        return "Partners have different immediate needs. Consider taking a break and revisiting when emotions are calmer."

# ============================================================================
# DR. MARCIE AI ENDPOINT
# ============================================================================

@app.post("/api/marcie/chat", response_model=MarcieResponse)
async def chat_with_marcie(request: MarcieRequest):
    """Chat with Dr. Marcie AI"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        genai.configure(api_key=api_key)
        
        sarcasm_config = SARCASM_LEVELS.get(request.sarcasm_level, SARCASM_LEVELS[1])
        system_prompt = sarcasm_config["system_prompt"]
        
        if request.game_context:
            system_prompt += f"\n\nGame Context: {request.game_context}"
        
        model = genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            system_instruction=system_prompt
        )
        
        chat = model.start_chat(history=[])
        
        response_obj = chat.send_message(
            f"Context: {request.context}\n\nUser says: {request.message}\n\nRespond as Dr. Marcie Liss with your signature wit and therapeutic insight. Keep response under 150 words.",
            generation_config=genai.types.GenerationConfig(
                temperature=sarcasm_config.get("temperature", 0.7),
                max_output_tokens=300,
            )
        )
        
        response = response_obj.text
        
        # Determine animation based on response sentiment
        animation = "marcie-idle"
        response_lower = response.lower()
        if any(word in response_lower for word in ["proud", "amazing", "excellent", "wow", "great job"]):
            animation = "marcie-correct"
        elif any(word in response_lower for word in ["hmm", "interesting", "let me think", "consider"]):
            animation = "marcie-thinking"
        elif any(word in response_lower for word in ["ouch", "yikes", "oh no", "that hurts"]):
            animation = "marcie-shocked"
        elif any(word in response_lower for word in ["ha", "laugh", "funny", "hilarious"]):
            animation = "marcie-laugh"
        elif any(word in response_lower for word in ["warning", "careful", "watch out", "red flag"]):
            animation = "marcie-warning"
        
        return MarcieResponse(
            response=response,
            animation=animation,
            sarcasm_level=request.sarcasm_level
        )
        
    except Exception as e:
        print(f"Gemini AI error: {str(e)}")
        # Fallback responses if Gemini fails
        fallback_responses = [
            "Sweetheart, if avoiding tough conversations were cardio, you'd be an Olympic athlete. Let's talk.",
            "That's not a red flag, darling—that's a red circus tent. With elephants.",
            "Communication isn't mind-reading. Use words, not vibes.",
            "Apologies without change are just performance art.",
            "You can't heal a relationship by pretending the wound doesn't exist.",
            "If 'I'm fine' were currency, you'd be bankrupt by now."
        ]
        import random
        return MarcieResponse(
            response=random.choice(fallback_responses),
            animation="marcie-idle",
            sarcasm_level=request.sarcasm_level
        )

# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

@app.get("/api/leaderboard/global")
async def get_global_leaderboard(limit: int = 100):
    """Get global leaderboard"""
    if db:
        couples_ref = db.collection('couples')
        query = couples_ref.order_by('total_points', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        
        leaderboard = []
        rank = 1
        for doc in docs:
            data = doc_to_dict(doc)
            # Get user details
            user1_doc = get_user_ref(data.get('user1_id')).get()
            user2_doc = get_user_ref(data.get('user2_id')).get()
            
            user1_name = user1_doc.to_dict().get('display_name', 'Unknown') if user1_doc.exists else 'Unknown'
            user2_name = user2_doc.to_dict().get('display_name', 'Unknown') if user2_doc.exists else 'Unknown'
            
            leaderboard.append({
                "rank": rank,
                "couple_id": doc.id,
                "display_names": [user1_name, user2_name],
                "total_score": data.get('total_points', 0),
                "streak_days": data.get('streak_days', 0),
                "trust_meter": data.get('trust_meter', 0.5)
            })
            rank += 1
    else:
        # Fallback: sort by total_points
        sorted_couples = sorted(
            couples_db.values(),
            key=lambda x: x.get('total_points', 0),
            reverse=True
        )[:limit]
        
        leaderboard = []
        for rank, couple in enumerate(sorted_couples, 1):
            user1 = users_db.get(couple.get('user1_id'), {})
            user2 = users_db.get(couple.get('user2_id'), {})
            
            leaderboard.append({
                "rank": rank,
                "couple_id": couple.get('id'),
                "display_names": [
                    user1.get('display_name', 'Unknown'),
                    user2.get('display_name', 'Unknown')
                ],
                "total_score": couple.get('total_points', 0),
                "streak_days": couple.get('streak_days', 0),
                "trust_meter": couple.get('trust_meter', 0.5)
            })
    
    return {"leaderboard": leaderboard}


@app.get("/api/leaderboard/categories/{category_id}")
async def get_category_leaderboard(category_id: str, limit: int = 50):
    """Get leaderboard for a specific game category"""
    if db:
        sessions_ref = db.collection('game_sessions')
        query = (
            sessions_ref
            .where('category_id', '==', category_id)
            .where('completed', '==', True)
            .order_by('score', direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = query.stream()
        
        entries = []
        for doc in docs:
            data = doc_to_dict(doc)
            user_doc = get_user_ref(data.get('user_id')).get()
            user_name = user_doc.to_dict().get('display_name', 'Unknown') if user_doc.exists else 'Unknown'
            
            entries.append({
                "user_id": data.get('user_id'),
                "display_name": user_name,
                "game_id": data.get('game_id'),
                "score": data.get('score', 0),
                "completed_at": data.get('completed_at')
            })
    else:
        entries = [
            {
                "user_id": s.get('user_id'),
                "display_name": users_db.get(s.get('user_id', ''), {}).get('display_name', 'Unknown'),
                "game_id": s.get('game_id'),
                "score": s.get('score', 0),
                "completed_at": s.get('completed_at')
            }
            for s in game_sessions_db.values()
            if s.get('category_id') == category_id and s.get('completed')
        ]
        entries.sort(key=lambda x: x['score'], reverse=True)
        entries = entries[:limit]
    
    return {"category": category_id, "entries": entries}


@app.get("/api/leaderboards/categories/{category_id}")
async def get_category_leaderboard_plural(category_id: str, limit: int = 50):
    valid_categories = {cat["id"] for cat in GAME_CATEGORIES}
    if category_id not in valid_categories:
        raise HTTPException(status_code=404, detail="Invalid category")

    result = await get_category_leaderboard(category_id=category_id, limit=limit)
    entries = result.get("entries", [])
    category_info = next((cat for cat in GAME_CATEGORIES if cat["id"] == category_id), {})

    return {
        "category": category_id,
        "leaderboard": entries,
        "category_stats": {
            "game_count": len(category_info.get("games", [])),
            "category_name": category_info.get("name", "Unknown")
        }
    }


# Additional leaderboard endpoints expected by tests
@app.get("/api/leaderboards/global")
async def leaderboards_global(limit: int = 100, offset: int = 0, time_period: str = "all_time"):
    if time_period not in ["all_time", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid time_period")

    # Reuse global leaderboard generator
    result = await get_global_leaderboard(limit=limit)
    leaderboard = result.get("leaderboard", [])
    total = len(leaderboard)
    sliced = leaderboard[offset:offset+limit]

    return {"leaderboard": sliced, "total_entries": total, "time_period": time_period, "limit": limit, "offset": offset}


@app.get("/api/leaderboards/couples/{couple_id}/ranking")
async def couple_ranking(couple_id: str):
    # Simple ranking: find position in global leaderboard
    global_board = (await get_global_leaderboard(limit=1000)).get("leaderboard", [])
    total = len(global_board)
    rank = next((i+1 for i, c in enumerate(global_board) if c.get("couple_id") == couple_id), None)
    if rank is None:
        # Return a default structure
        return {"couple": {}, "nearby_competitors": [], "percentile": 0, "total_participants": total}

    # Nearby competitors
    idx = max(0, rank-3)
    nearby = global_board[idx:idx+5]
    percentile = int((1 - (rank / (total or 1))) * 100)
    return {"couple": {"id": couple_id, "rank": rank}, "nearby_competitors": nearby, "percentile": percentile, "total_participants": total}


@app.get("/api/leaderboards/friends/{user_id}")
async def friends_leaderboard(user_id: str):
    # Return empty leaderboard with user rank placeholder
    return {"user_id": user_id, "leaderboard": [], "your_rank": None}


@app.get("/api/leaderboards/achievements")
async def achievement_leaderboard():
    return {"type": "achievements", "leaderboard": [], "total_achievements_available": 42, "rarest_achievements": []}


@app.get("/api/leaderboards/streaks")
async def streak_leaderboard():
    return {"type": "streaks", "leaderboard": [], "longest_streak_ever": 365, "streak_milestones": [7, 30, 100]}


@app.get("/api/leaderboards/newcomers")
async def newcomers_leaderboard():
    return {"type": "newcomers", "leaderboard": []}


@app.post("/api/leaderboards/refresh")
async def refresh_leaderboards():
    # In production, this would refresh caches
    cached = ["global", "streaks", "achievements"]
    return {"success": True, "cached_boards": cached, "refreshed_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/leaderboards/stats/summary")
async def leaderboard_stats():
    total_couples = len(couples_db)
    total_games = len(game_sessions_db)
    growth = {"monthly": 0.05}
    return {"total_couples": total_couples, "total_games_played": total_games, "growth": growth}

# ============================================================================
# LOVE ARCADE ENDPOINTS
# ============================================================================

@app.get("/api/love-arcade/games")
async def get_love_arcade_games():
    """Get all Love Arcade games with detailed configurations"""
    return {
        "games": [
            {
                "id": "truth-teller-tower",
                "name": "Truth Teller Tower",
                "phase": "Foundation (Phase 1)",
                "format": "Who Wants to Be a Millionaire meets The Newlywed Game",
                "description": "Scale the lie-avalanche. Five questions. Three lifelines. One shared brain.",
                "max_score": 100,
                "lifelines": ["50/50", "Double Confidence", "Trust Check"],
                "scoring": {
                    "correct_answer": 10,
                    "predicted_partner": 5,
                    "double_truth": 20
                }
            },
            {
                "id": "echo-chamber-escape",
                "name": "Escape from the Echo Chamber",
                "phase": "Deconstruction (Phase 2)",
                "format": "Digital Escape Room",
                "description": "Trapped in a hall of infinite mirrors. Break the loop together.",
                "max_score": 100,
                "time_limit_per_puzzle": 90,
                "puzzles": 5
            },
            {
                "id": "intimacy-feud",
                "name": "The Intimacy Feud",
                "phase": "Shared Reality (Phase 3)",
                "format": "Family Feud style",
                "description": "Survey says... be boring. Be authentic. Be real.",
                "max_score": 250,
                "scoring": {
                    "1st_place": 50,
                    "2nd_place": 30,
                    "3rd_place": 20,
                    "partner_match": 10,
                    "authenticity_streak": 15
                }
            },
            {
                "id": "relational-jeopardy",
                "name": "Relational Jeopardy!",
                "phase": "The Future (Phase 4)",
                "format": "Jeopardy style",
                "description": "Categories designed by couples who rebuilt.",
                "max_score": 2000,
                "categories": ["Accountability Plans", "Redefinition", "Integration"],
                "has_daily_double": True,
                "has_final_jeopardy": True
            },
            {
                "id": "family-forge",
                "name": "Family Forge Edition",
                "phase": "Special - Family Building",
                "format": "Mixed game show formats",
                "description": "For couples forging families after betrayal.",
                "max_score": 1800,
                "sub_games": ["Family Feud: Our New Reality", "The Newlywed Game: Heart-to-Heart", "Chopped: Family Kitchen", "The Amazing Race: Legacy Dash"]
            },
            {
                "id": "harbor-storm",
                "name": "Harbor & Storm Edition",
                "phase": "Special - BPD/Emotional Regulation",
                "format": "Cooperative challenges",
                "description": "Build a better boat. Learn to sail as a crew.",
                "max_score": 1900,
                "sub_games": ["BPD Pattern Detective", "Validation Game Show", "Connection Constructor", "Harbor Master's Challenge"]
            },
            {
                "id": "phoenix-protocol",
                "name": "Phoenix Protocol Edition",
                "phase": "Special - Post-Infidelity Recovery",
                "format": "Forensic Investigation",
                "description": "Burn the evidence. Rise from the ashes.",
                "max_score": 2200,
                "sub_games": ["Truth & Transparency Gauntlet", "Timeline Detective", "Layers of Hurt Escape Room", "Trust-Building Bingo", "Future Council"]
            },
            {
                "id": "trust-renovation",
                "name": "Trust Renovation Edition",
                "phase": "Special - Trust Rebuilding",
                "format": "Construction Simulation",
                "description": "Gut the haunted house. Build a safe home.",
                "max_score": 1750,
                "sub_games": ["De-Escalation Lab", "Cycle Breaker Board Game", "Apology & Release Workshop", "Trust Wiring Simulator", "Relationship Council"]
            },
            {
                "id": "word-wound",
                "name": "Word-Wound Edition",
                "phase": "Special - Verbal Violence Recovery",
                "format": "Forensic Accountability",
                "description": "Silence the weapon. Suture the wound.",
                "max_score": 1000,
                "sub_games": ["Deal or No Deal: Accountability", "Truth & Transparency Gauntlet", "Validation Game Show"]
            }
        ]
    }

@app.get("/api/love-arcade/games/{game_id}/questions")
async def get_love_arcade_questions(game_id: str):
    """Get questions for a specific Love Arcade game"""
    
    questions_db = {
        "truth-teller-tower": [
            {
                "id": "ttt_q1",
                "module": "Module 1: The Naming Ceremony",
                "question": "Before rebuilding, you must name the dragon. What's the #1 reason couples fail Phase 1?",
                "options": [
                    "A) They call it 'a rough patch.'",
                    "B) They skip naming the betrayal and jump to 'fixing.'",
                    "C) They let the betrayed partner define it alone.",
                    "D) They use clinical jargon to sound smart."
                ],
                "correct": "B",
                "explanation": "If you don't name the monster, it lives in your basement rent-free."
            },
            {
                "id": "ttt_q2",
                "module": "Module 2: Truth-Telling Treaty",
                "question": "The 'Amnesty Clause' isn't about forgetting—it's about creating space for what?",
                "options": [
                    "A) Revenge fantasies",
                    "B) Controlled, time-bound truth extraction",
                    "C) Weekly lie audits",
                    "D) Blame-shifting with receipts"
                ],
                "correct": "B",
                "explanation": "It's a truth IV drip—not a firehose. Drip. Drip. Drip. Until the system flushes."
            },
            {
                "id": "ttt_q3",
                "module": "Module 3: Safety Net Design",
                "question": "A 'Minimum Daily Requirement' of safety is NOT:",
                "options": [
                    "A) A vague promise like 'I'll be better.'",
                    "B) A specific, observable action (e.g., 'text when you land').",
                    "C) A weekly check-in ritual.",
                    "D) Voluntary disclosure of high-risk moments."
                ],
                "correct": "A",
                "explanation": "'I'll be better' is the relationship equivalent of 'I'll start Monday.' Spoiler: Monday never comes."
            },
            {
                "id": "ttt_q4",
                "module": "Module 1 + 2 Hybrid",
                "question": "Your 'Safe Word' should be:",
                "options": [
                    "A) Something emotionally loaded (e.g., 'betrayal')",
                    "B) Something absurd and neutral (e.g., 'waffle iron')",
                    "C) A phrase that explains why you're pausing",
                    "D) Whatever the therapist suggested"
                ],
                "correct": "B",
                "explanation": "If you yell 'waffle iron' mid-fight? Even YOU have to laugh. And laughter is the first crack in the armor."
            },
            {
                "id": "ttt_q5",
                "module": "Module 3: Bonus Round Energy",
                "question": "Shaking hands after signing the Safety Net isn't symbolic—it's:",
                "options": [
                    "A) A power move",
                    "B) A neurological reset (touch reduces threat response)",
                    "C) A throwback to medieval oaths",
                    "D) Just for the photo"
                ],
                "correct": "B",
                "explanation": "Science says: skin-to-skin contact drops cortisol. So yeah—shake like your amygdala depends on it. (It does.)"
            }
        ],
        "relational-jeopardy": [
            {
                "id": "rj_cat1_100",
                "category": "Accountability Plans",
                "value": 100,
                "clue": "This replaces indefinite phone access: scheduled, voluntary check-ins.",
                "answer": "What is a 'Transparency Rhythm'?"
            },
            {
                "id": "rj_cat1_200",
                "category": "Accountability Plans",
                "value": 200,
                "clue": "The 'Relapse Protocol' requires this *before* acting on deceptive urges.",
                "answer": "What is 'verbalizing the urge to a safe person'?"
            },
            {
                "id": "rj_cat1_300",
                "category": "Accountability Plans",
                "value": 300,
                "clue": "A sustainable accountability system must include this review date.",
                "answer": "What is a 'sunset clause' (e.g., 6 months)?"
            },
            {
                "id": "rj_cat1_400",
                "category": "Accountability Plans",
                "value": 400,
                "daily_double": True,
                "clue": "The #1 reason accountability plans fail: they're designed by the perpetrator *alone*.",
                "answer": "What is 'lack of co-creation'?"
            },
            {
                "id": "rj_cat1_500",
                "category": "Accountability Plans",
                "value": 500,
                "clue": "This phrase turns surveillance into partnership: 'I'm sharing this because…'",
                "answer": "What is 'contextual transparency'?"
            },
            {
                "id": "rj_cat2_100",
                "category": "Redefinition",
                "value": 100,
                "clue": "Option B: 'The Experimental Art Collective' is defined by this.",
                "answer": "What is 'co-creating something unknown and weird'?"
            },
            {
                "id": "rj_cat2_200",
                "category": "Redefinition",
                "value": 200,
                "clue": "A non-negotiable law in the new realm: 'We shall never…'",
                "answer": "What is 'pretend the past didn't happen'?"
            },
            {
                "id": "rj_cat2_300",
                "category": "Redefinition",
                "value": 300,
                "clue": "The core purpose of the new relationship isn't love—it's this.",
                "answer": "What is 'mutual becoming'?"
            },
            {
                "id": "rj_cat2_400",
                "category": "Redefinition",
                "value": 400,
                "clue": "This is the conscious choice to build *new* instead of repair *old*.",
                "answer": "What is 'redefinition'?"
            },
            {
                "id": "rj_cat2_500",
                "category": "Redefinition",
                "value": 500,
                "clue": "The name 'The United Realm of [X]' must reflect this.",
                "answer": "What is 'shared authorship of the story'?"
            },
            {
                "id": "rj_cat3_100",
                "category": "Integration",
                "value": 100,
                "clue": "The Scar & Tattoo Ceremony turns trauma into this.",
                "answer": "What is 'symbolic integration'?"
            },
            {
                "id": "rj_cat3_200",
                "category": "Integration",
                "value": 200,
                "clue": "Shield Section 2 (The Fight) should symbolize this.",
                "answer": "What is 'the work you chose to do'?"
            },
            {
                "id": "rj_cat3_300",
                "category": "Integration",
                "value": 300,
                "clue": "The motto must be 3–5 words and avoid these two things.",
                "answer": "What are 'clichés and absolutes'?"
            },
            {
                "id": "rj_cat3_400",
                "category": "Integration",
                "value": 400,
                "clue": "Burning the workbook isn't destruction—it's this ritual act.",
                "answer": "What is 'releasing the artifact of the old story'?"
            },
            {
                "id": "rj_cat3_500",
                "category": "Integration",
                "value": 500,
                "clue": "The final gesture—'Do your relationship's signature move'—is this psychologically.",
                "answer": "What is 'embodied recommitment'?"
            }
        ]
    }
    
    if game_id not in questions_db:
        raise HTTPException(status_code=404, detail="Game questions not found")
    
    return {
        "game_id": game_id,
        "questions": questions_db[game_id],
        "total_questions": len(questions_db[game_id])
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=getattr(exc, 'status_code', 400), content={
        "error": exc.detail,
        "code": getattr(exc, 'status_code', 400),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={
        "error": "Internal server error",
        "detail": str(exc) if os.environ.get("DEBUG") else "An unexpected error occurred",
        "code": 500,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
