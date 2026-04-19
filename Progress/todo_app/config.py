import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'todo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID', '')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET', '')
    OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/auth/oauth/callback/google')
    
    # Pomodoro Settings
    POMODORO_WORK = int(os.environ.get('POMODORO_WORK', 25))
    POMODORO_SHORT_BREAK = int(os.environ.get('POMODORO_SHORT_BREAK', 5))
    POMODORO_LONG_BREAK = int(os.environ.get('POMODORO_LONG_BREAK', 15))
