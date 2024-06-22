from flask import Flask,session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from supabase import create_client, Client
from DB_utils.confing import DBConfig

db = SQLAlchemy()
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
print(template_folder)

def create_app():
    app = Flask('__main__', static_folder=static_folder, template_folder=template_folder)
    app.config.from_object(DBConfig)
    db.init_app(app)
    app.config['SESSION_SQLALCHEMY'] = db
    
    with app.app_context():
        from DB_utils import models
        # Initialize the Flask-Session extension TODO
        
        db.create_all()
        # Set the SQLAlchemy session instance to the app config
        app.config['SESSION_SQLALCHEMY'] = db
    db.metadata.clear()
    Session(app)
    # Initialize Supabase client
    app.supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SERVICE_ROLE_KEY'])
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    return app
