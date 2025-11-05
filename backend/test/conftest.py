from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

# Apunta a .../multitop-demand-system/backend
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # app = create_app() en app/main.py

@pytest.fixture(scope="session")
def client():
    return TestClient(app)