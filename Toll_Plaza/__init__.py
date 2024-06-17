from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from supabase import create_client, Client
from DB_utils.confing import DBConfig
from supabase import create_client, Client
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(DBConfig)
    db.init_app(app)

    with app.app_context():
        print("Inside\n\n")
        from DB_utils import models
        db.create_all()
        # Set the SQLAlchemy session instance to the app config
        app.config['SESSION_SQLALCHEMY'] = db
        
    # Initialize the Flask-Session extension
    # Initialize Supabase client
    app.supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    return app
