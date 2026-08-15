import os
import sys

# Ensure root directory is added to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the FastAPI app from web_app/server.py
from web_app.server import app
