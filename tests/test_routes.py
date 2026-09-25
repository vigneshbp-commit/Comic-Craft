import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Set fast procedural backend and isolated test environment to preserve live API quotas
os.environ["IMAGE_GEN_BACKEND"] = "procedural"
os.environ["GEMINI_API_KEY"] = ""
from app.config import settings
settings.IMAGE_GEN_BACKEND = "procedural"
settings.GEMINI_API_KEY = ""

from app.main import app

client = TestClient(app)


def test_home_route():
    """Verify GET / returns homepage with 200 OK and form elements."""
    response = client.get("/")
    assert response.status_code == 200
    assert "COMICCRAFT" in response.text
    assert "CREATE YOUR AI COMIC BOOK" in response.text
    assert 'name="story_prompt"' in response.text
    assert 'name="character_name"' in response.text


def test_health_route():
    """Verify GET /health returns status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "ComicCraft"


def test_test_image_get():
    """Verify GET /test-image creates an image and returns JSON."""
    response = client.get("/test-image?prompt=A+brave+robot+in+the+rain")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["image_url"].startswith("/static/panels/")
    assert os.path.exists(data["image_path"])


def test_test_image_post():
    """Verify POST /test-image endpoint."""
    payload = {
        "prompt": "Cyberpunk samurai under red neon sign",
        "panel_number": 2,
        "art_style": "Anime"
    }
    response = client.post("/test-image", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "image_url" in data
    assert os.path.exists(data["image_path"])


def test_generate_form_post():
    """Verify POST /generate returns rendered comic_preview.html with all 5 panels."""
    form_data = {
        "story_prompt": "A brave fox exploring an enchanted forest",
        "character_name": "Rusty",
        "setting": "Enchanted Forest",
        "tone": "Dramatic",
        "art_style": "Comic Book"
    }
    response = client.post("/generate", data=form_data)
    assert response.status_code == 200
    assert "STORY PREVIEW" in response.text
    assert "PANEL #1" in response.text
    assert "PANEL #5" in response.text
    assert "Download Comic as PDF" in response.text


def test_generate_comic_json():
    """Verify POST /generate-comic/json returns JSON response with 5 panels and PDF."""
    payload = {
        "story_prompt": "A young wizard discovering an ancient spellbook in a hidden library",
        "character_name": "Lyra",
        "setting": "Ancient Ruins",
        "tone": "Mystery",
        "art_style": "Comic Book"
    }
    response = client.post("/generate-comic/json", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["panels"]) == 5
    assert data["pdf_url"].startswith("/static/exports/")
    assert os.path.exists(data["pdf_path"])


def test_export_success_route():
    """Verify GET /export-success displays confirmation."""
    response = client.get("/export-success?pdf_url=/static/exports/test.pdf&title=Test+Comic")
    assert response.status_code == 200
    assert "COMIC EXPORTED SUCCESSFULLY!" in response.text
    assert "GO CREATE ANOTHER COMIC" in response.text


def test_download_pdf_route():
    """Verify GET /download-pdf/{filename} returns the file."""
    # First generate a comic via JSON to get a real PDF
    payload = {
        "story_prompt": "A starship captain navigating an asteroid belt",
        "character_name": "Captain Nova",
        "setting": "Deep Space",
        "tone": "Action-packed",
        "art_style": "Realistic"
    }
    res = client.post("/generate-comic/json", json=payload)
    data = res.json()
    pdf_filename = Path(data["pdf_path"]).name

    # Now download it
    dl_res = client.get(f"/download-pdf/{pdf_filename}")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) > 500
