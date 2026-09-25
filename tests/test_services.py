import os
from pathlib import Path
from PIL import Image
import pytest

os.environ["IMAGE_GEN_BACKEND"] = "procedural"
os.environ["GEMINI_API_KEY"] = ""
from app.config import settings
settings.IMAGE_GEN_BACKEND = "procedural"
settings.GEMINI_API_KEY = ""

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image, sanitize_filename
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


def test_generate_outline():
    """Verify Gemini Flash outline generation produces 5 structured panels."""
    outline = generate_outline(
        story_prompt="A brave fox exploring an enchanted forest",
        character_name="Rusty",
        setting="Enchanted Forest",
        tone="Dramatic",
        art_style="Comic Book"
    )

    assert isinstance(outline, list)
    assert len(outline) == 5

    for i, panel in enumerate(outline, start=1):
        assert panel["panel_number"] == i
        assert "title" in panel and len(panel["title"]) > 0
        assert "scene_description" in panel and len(panel["scene_description"]) > 0
        assert "image_prompt" in panel and len(panel["image_prompt"]) > 0


def test_generate_story():
    """Verify Gemini Pro generates dialogues, captions, and narration for all panels."""
    outline = generate_outline(
        story_prompt="A brave fox exploring an enchanted forest",
        character_name="Rusty",
        setting="Enchanted Forest",
        tone="Dramatic",
        art_style="Comic Book"
    )

    story_panels = generate_story(
        outline=outline,
        character_name="Rusty",
        setting="Enchanted Forest",
        tone="Dramatic"
    )

    assert isinstance(story_panels, list)
    assert len(story_panels) == 5

    for i, panel in enumerate(story_panels, start=1):
        assert panel["panel_number"] == i
        assert "caption" in panel and len(panel["caption"]) > 0
        assert "dialogue" in panel
        assert "narration" in panel and len(panel["narration"]) > 0
        assert "full_text" in panel


def test_generate_image():
    """Verify image generator creates a valid, readable PNG file on disk."""
    prompt = "Rusty the fox finding a glowing relic in an ancient glowing forest"
    web_url, local_path = generate_image(prompt=prompt, panel_number=1, art_style="Comic Book")

    assert web_url.startswith("/static/panels/")
    assert os.path.exists(local_path)
    assert Path(local_path).stat().st_size > 0

    # Verify Pillow can open the generated image
    with Image.open(local_path) as img:
        assert img.format == "PNG"
        assert img.width > 200
        assert img.height > 200


def test_layout_builder():
    """Verify layout builder cleanly merges outlines, stories, and image paths."""
    outline = [
        {"panel_number": 1, "title": "The Journey Begins", "scene_description": "Rusty enters the forest", "image_prompt": "Prompt 1"}
    ]
    story_panels = [
        {"panel_number": 1, "caption": "CHAPTER 1", "narration": "Rusty stepped forward.", "dialogue": 'Rusty: "Here we go!"', "full_text": "Full 1"}
    ]
    image_data = [
        {"panel_number": 1, "image_url": "/static/panels/p1.png", "image_path": "/fake/p1.png"}
    ]

    layout = build_comic_layout(outline, story_panels, image_data)
    assert len(layout) == 1
    panel = layout[0]
    assert panel["panel_number"] == 1
    assert panel["title"] == "The Journey Begins"
    assert panel["image_url"] == "/static/panels/p1.png"
    assert panel["caption"] == "CHAPTER 1"
    assert panel["narration"] == "Rusty stepped forward."


def test_save_pdf():
    """Verify PDF compilation exports a valid multi-page PDF file."""
    # Generate a dummy image first
    _, test_img_path = generate_image("Test scene for PDF", panel_number=1, art_style="Comic Book")

    layout = [
        {
            "panel_number": 1,
            "title": "Into the Unknown",
            "scene_description": "The deep forest looms.",
            "caption": "MEANWHILE IN THE FOREST...",
            "narration": "A shadowy wind blew softly across the glade.",
            "dialogue": 'Rusty: "We must be cautious."',
            "full_text": "Text 1",
            "image_url": "/static/panels/test.png",
            "image_path": test_img_path,
            "image_prompt": "Test scene prompt"
        }
    ]

    pdf_url, pdf_path = save_pdf(
        layout_data=layout,
        story_title="Rusty's Grand Adventure",
        character_name="Rusty",
        setting="Enchanted Forest",
        tone="Dramatic",
        art_style="Comic Book"
    )

    assert pdf_url.startswith("/static/exports/")
    assert os.path.exists(pdf_path)
    assert Path(pdf_path).stat().st_size > 500  # Non-trivial size
