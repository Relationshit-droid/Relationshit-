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
    from server import db, get_sos_ref, get_couple_ref, get_user_ref
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = db is not None
except ImportError:
    FIREBASE_AVAILABLE = False
    db = None
    get_sos_ref = None
    get_couple_ref = None
    get_user_ref = None

# ... (rest of file unchanged, copy original content from sha b93371b2b2ac4720c40773ecaa492076115b64c4 but with this import fix)