"""
Firebase Admin SDK initialization and Firestore client singleton.
"""
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def get_db():
    """Return (and lazily initialize) the Firestore client."""
    global _db
    if _db is not None:
        return _db

    svc_account = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

    if not firebase_admin._apps:
        if os.path.isfile(svc_account):
            cred = credentials.Certificate(svc_account)
        elif svc_account.strip().startswith("{"):
            cred = credentials.Certificate(json.loads(svc_account))
        else:
            # Fall back to Application Default Credentials (Cloud Run)
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
