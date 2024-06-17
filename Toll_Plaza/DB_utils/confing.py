from datetime import timedelta
import os
from dotenv import load_dotenv
load_dotenv()
# Check if environment variables are loaded
print("SUPABASE_CONNECTION:", os.environ.get("SUPABASE_CONNECTION"))
print("SUPABASE_URL:", os.environ.get("SUPABASE_URL"))
print("SUPABASE_KEY:", os.environ.get("SUPABASE_KEY"))
class DBConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get("SUPABASE_CONNECTION")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    SESSION_SQLALCHEMY = None  # Will be set in __init__.py
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_STORAGE_BUCKET = 'profile-pics'

