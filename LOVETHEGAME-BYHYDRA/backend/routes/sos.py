"""
SOS Crisis System Routes
Handles panic button, crisis resources, and de-escalation
Production-ready with Firebase Firestore integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import uuid

# Firebase imports
try:
    from server import db, get_sos_ref, get_couple_ref, get_user_ref, doc_to_dict
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = db is not None
except ImportError:
    FIREBASE_AVAILABLE = False
    db = None
    get_sos_ref = None
    get_couple_ref = None
    get_user_ref = None
    doc_to_dict = None

router = APIRouter(prefix="/api/sos", tags=["sos"])

# In-memory fallback storage
sos_sessions_db: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Pydantic Models
# =============================================================================

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


class SOSResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


class SOSEscalateRequest(BaseModel):
    reason: Optional[str] = None


class SOSAnalyzeResult(BaseModel):
    verdict: str
    status: str


# =============================================================================
# Helpers
# =============================================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_session(session_id: str) -> Dict[str, Any]:
    if db and get_sos_ref:
        doc = get_sos_ref(session_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="SOS Session not found")
        return doc_to_dict(doc)
    session = sos_sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="SOS Session not found")
    return session


def _save_session(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    if db and get_sos_ref:
        get_sos_ref(session_id).update(updates)
        return doc_to_dict(get_sos_ref(session_id).get())
    sos_sessions_db[session_id].update(updates)
    return sos_sessions_db[session_id]


# =============================================================================
# Session Lifecycle Endpoints
# =============================================================================

@router.post("/sessions", response_model=None)
async def create_sos_session(sos: SOSSessionCreate):
    """Create a new SOS fight resolution session"""
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    new_session = {
        "id": session_id,
        "initiator_id": sos.initiator_id,
        "couple_id": sos.couple_id,
        "status": "waiting_for_partner",
        "started_at": _now_iso(),
        "submissions": {},
        "verdict": None,
        "expires_at": expires_at
    }

    if db and get_sos_ref:
        get_sos_ref(session_id).set(new_session)
    else:
        sos_sessions_db[session_id] = new_session

    return new_session


@router.get("/sessions/{session_id}")
async def get_sos_session(session_id: str):
    """Get SOS session by ID"""
    return _get_session(session_id)


@router.post("/sessions/{session_id}/submit")
async def submit_sos_booth(session_id: str, submission: SOSBoothSubmission):
    """Submit SOS booth response"""
    session = _get_session(session_id)

    expires_at = session.get("expires_at")
    if expires_at and datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        _save_session(session_id, {"status": "expired"})
        raise HTTPException(status_code=400, detail="SOS Session has expired")

    submission_data = {
        "i_feel": submission.i_feel,
        "when_partner": submission.when_partner,
        "because_i_tell_myself": submission.because_i_tell_myself,
        "what_i_need": submission.what_i_need,
        "submitted_at": _now_iso()
    }

    submissions = dict(session.get("submissions", {}))
    submissions[submission.user_id] = submission_data

    status = "analyzing" if len(submissions) >= 2 else "one_submitted" if len(submissions) == 1 else "waiting_for_partner"
    return _save_session(session_id, {"submissions": submissions, "status": status})


@router.post("/sessions/{session_id}/analyze")
async def analyze_sos_session(session_id: str):
    """Trigger AI analysis of SOS session"""
    session = _get_session(session_id)

    submissions = session.get("submissions", {})
    if len(submissions) < 2:
        raise HTTPException(status_code=400, detail="Both partners must submit before analysis")

    verdict = generate_sos_verdict(submissions)
    return _save_session(session_id, {
        "verdict": verdict,
        "status": "completed",
        "completed_at": _now_iso()
    })


@router.post("/{session_id}/resolve")
async def resolve_sos(session_id: str, payload: SOSResolveRequest):
    """Mark an SOS session as resolved"""
    session = _get_session(session_id)
    _save_session(session_id, {
        "status": "resolved",
        "resolved_at": _now_iso(),
        "resolution_notes": payload.resolution_notes
    })
    return {"success": True, "resolved_at": _now_iso()}


@router.post("/{session_id}/escalate")
async def escalate_sos(session_id: str, payload: SOSEscalateRequest):
    """Escalate an SOS session with immediate crisis resources"""
    _get_session(session_id)
    _save_session(session_id, {"status": "escalated", "escalated_at": _now_iso(), "reason": payload.reason})
    return {
        "success": True,
        "status": "escalated",
        "immediate_resources": ["988 Hotline", "Local Emergency Services"]
    }


# =============================================================================
# Crisis Resources
# =============================================================================

@router.get("/resources")
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


@router.get("/resources/recommended")
async def get_recommended_resources(user_id: str, severity: int = 3):
    if severity >= 4:
        recs = ["988 Hotline", "grounding", "seek-professional-help"]
    else:
        recs = ["breathing-exercise", "repair-attempt"]
    return {"user_id": user_id, "severity": severity, "recommendations": recs}


# =============================================================================
# Verdict Generation
# =============================================================================

def generate_sos_verdict(submissions: Dict[str, Any]) -> str:
    """Generate an AI-based verdict from SOS submissions"""
    user_ids = list(submissions.keys())
    if len(user_ids) < 2:
        return "Insufficient data for analysis"

    sub1 = submissions[user_ids[0]]
    sub2 = submissions[user_ids[1]]

    common_themes = ["listen", "understand", "support", "time", "space"]
    need1 = str(sub1.get("what_i_need", "")).lower()
    need2 = str(sub2.get("what_i_need", "")).lower()

    needs_overlap = any(theme in need1 and theme in need2 for theme in common_themes)

    if needs_overlap:
        return "Both partners are seeking understanding and connection. Focus on active listening and validation."
    return "Partners have different immediate needs. Consider taking a break and revisiting when emotions are calmer."
