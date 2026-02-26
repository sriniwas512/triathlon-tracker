import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

_db = None

def get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
            if not service_account_json:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set")
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db
