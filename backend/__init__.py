import sys
import os

# Add the backend directory to sys.path so bare imports work
# when the app is run as a package (uvicorn backend.main:app)
sys.path.insert(0, os.path.dirname(__file__))
