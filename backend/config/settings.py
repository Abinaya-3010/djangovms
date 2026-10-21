from pathlib import Path
import os
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/'.env')
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','dev-only-insecure-key')
DEBUG=os.getenv('DEBUG','False').lower()=='true'
ALLOWED_HOSTS=['localhost','127.0.0.1']
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.staticfiles','rest_framework','corsheaders','vms']
MIDDLEWARE=['corsheaders.middleware.CorsMiddleware','django.middleware.common.CommonMiddleware','django.contrib.sessions.middleware.SessionMiddleware']
ROOT_URLCONF='config.urls'
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('DB_NAME','vendorpro_db'),'USER':os.getenv('DB_USER','postgres'),'PASSWORD':os.getenv('DB_PASSWORD',''),'HOST':os.getenv('DB_HOST','localhost'),'PORT':os.getenv('DB_PORT','5432')}}
CORS_ALLOWED_ORIGINS=['http://localhost:9000','http://localhost:5173']
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':[],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.AllowAny']}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
MEDIA_ROOT=BASE_DIR/'uploads'
MEDIA_URL='/uploads/'
USE_TZ=True
TIME_ZONE='UTC'
# Static files configuration
STATIC_URL = "/static/"
