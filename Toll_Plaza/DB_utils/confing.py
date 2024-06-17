from datetime import timedelta
import os
from dotenv import load_dotenv
load_dotenv()

class DBConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get("SUPABASE_CONNECTION")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'useressions'
    SESSION_SQLALCHEMY = None  # Will be set in __init__.py
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = ''
    
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_STORAGE_BUCKET = 'profile-pics'
    
   
    

