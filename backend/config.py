from dotenv import load_dotenv
import os
load_dotenv()
class Settings:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
settings=Settings()