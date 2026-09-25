import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from app.config import EXPORTS_DIR

logger = logging.getLogger(__name__)


def _sanitize_for_pdf(text: str) -> str:
    """Sanitizes text to safe ASCII/Latin-1 characters for standard PDF fonts."""
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": " - ",
        "\u2013": " - ",
        "\u2026": "...",
        "\u2022": "*",
        "\u00a0": " ",
        "’": "'",
        "“": '"',
        "”": '"'
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Filter out characters that standard Latin-1 fpdf core fonts cannot render
    return text.encode("latin-1", "replace").decode("latin-1")


class ComicPDF:
    """PDF Builder for ComicCraft storyboards using fpdf2."""

    def __init__(self, title: str = "ComicCraft Adventure"):
        try:
            from fpdf import FPDF
            self.pdf_class = FPDF
        except ImportError:
            from fpdf2 import FPDF
            self.pdf_class = FPDF

        self.pdf = self.pdf_class(orientation="P", unit="mm", format="A4")
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.title = _sanitize_for_pdf(title)

    def add_cover_page(self, character_name: str, setting: str, tone: str, art_style: str):
        """Creates an attractive comic book title cover page."""
        self.pdf.add_page()

        # Outer comic decorative frame
        self.pdf.set_line_width(1.5)
        self.pdf.set_draw_color(30, 30, 30)
        self.pdf.rect(10, 10, 190, 277)
        self.pdf.set_line_width(0.5)
        self.pdf.rect(12, 12, 186, 273)

        # Header badge
        self.pdf.set_fill_color(255, 225, 53)  # Comic Yellow
        self.pdf.rect(20, 25, 170, 24, "FD")
        self.pdf.set_font("Helvetica", "B", 18)
        self.pdf.set_text_color(20, 20, 20)
        self.pdf.set_xy(20, 30)
        self.pdf.cell(170, 12, "COMICCRAFT PRESENTS", border=0, align="C")

        # Main Title
        self.pdf.set_font("Helvetica", "B", 24)
        self.pdf.set_text_color(220, 38, 38)  # Comic Red
        self.pdf.set_xy(20, 60)
        self.pdf.multi_cell(170, 12, self.title.upper(), align="C")

        # Comic metadata badges
        self.pdf.set_y(105)
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(50, 50, 50)

        meta_items = [
            f"Protagonist: {_sanitize_for_pdf(character_name)}",
            f"Setting: {_sanitize_for_pdf(setting)}",
            f"Tone: {_sanitize_for_pdf(tone)}",
            f"Visual Art Style: {_sanitize_for_pdf(art_style)}",
            f"Created: {time.strftime('%Y-%m-%d %H:%M')}"
        ]

        for item in meta_items:
            self.pdf.set_fill_color(245, 247, 250)
            self.pdf.set_draw_color(200, 200, 200)
            self.pdf.cell(170, 10, f"  {item}", border=1, fill=True, align="L", new_x="LMARGIN", new_y="NEXT")
            self.pdf.ln(3)

        # Bottom Comic Blurb
        self.pdf.set_y(220)
        self.pdf.set_fill_color(30, 30, 30)
        self.pdf.rect(20, 220, 170, 45, "F")
        self.pdf.set_font("Helvetica", "I", 11)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_xy(25, 226)
        blurb = (
            "Generated with ComicCraft AI using Google Gemini models for storytelling and "
            "Diffusers / Comic Canvas for vivid comic book illustrations."
        )
        self.pdf.multi_cell(160, 6, _sanitize_for_pdf(blurb), align="C")

    def add_panel_page(self, panel: Dict[str, Any]):
        """Adds a neat, beautifully organized page for each panel."""
        self.pdf.add_page()
        p_num = panel.get("panel_number", 1)
        title = _sanitize_for_pdf(panel.get("title", f"Panel {p_num}"))
        scene_desc = _sanitize_for_pdf(panel.get("scene_description", ""))
        caption = _sanitize_for_pdf(panel.get("caption", ""))
        dialogue = _sanitize_for_pdf(panel.get("dialogue", ""))
        narration = _sanitize_for_pdf(panel.get("narration", ""))
        img_path = panel.get("image_path", "")

        # Page Border
        self.pdf.set_line_width(0.8)
        self.pdf.set_draw_color(40, 40, 40)
        self.pdf.rect(10, 10, 190, 277)

        # Panel Title Banner
        self.pdf.set_fill_color(255, 225, 53)
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.pdf.rect(15, 14, 180, 12, "FD")
        self.pdf.set_font("Helvetica", "B", 13)
        self.pdf.set_text_color(20, 20, 20)
        self.pdf.set_xy(15, 15)
        self.pdf.cell(180, 10, f"PANEL #{p_num}: {title.upper()}", align="C")

        # Illustration Frame
        img_y = 30
        img_w = 160
        img_h = 100

        if img_path and os.path.exists(img_path):
            try:
                # Center the image horizontally on A4 (width 210mm, margin = 25mm)
                self.pdf.image(img_path, x=25, y=img_y, w=img_w, h=img_h)
                # Outer stroke for the image
                self.pdf.rect(25, img_y, img_w, img_h)
            except Exception as e:
                logger.warning("Could not embed image in PDF: %s", e)
                self.pdf.set_xy(25, img_y)
                self.pdf.set_fill_color(230, 230, 230)
                self.pdf.rect(25, img_y, img_w, img_h, "FD")
                self.pdf.set_font("Helvetica", "I", 10)
                self.pdf.set_text_color(100, 100, 100)
                self.pdf.cell(img_w, img_h, "[Illustration]", align="C")
        else:
            self.pdf.set_xy(25, img_y)
            self.pdf.set_fill_color(240, 240, 240)
            self.pdf.rect(25, img_y, img_w, img_h, "FD")
            self.pdf.cell(img_w, img_h, "[Illustration Placeholder]", align="C")

        current_y = img_y + img_h + 8

        # Scene description (In italics, as specified in the project docs!)
        if scene_desc:
            self.pdf.set_xy(18, current_y)
            self.pdf.set_font("Helvetica", "I", 10)
            self.pdf.set_text_color(70, 70, 70)
            self.pdf.multi_cell(174, 5, f'Scene Context: "{scene_desc}"', align="L")
            current_y = self.pdf.get_y() + 4

        # Caption box (Highlighted comic caption)
        if caption:
            self.pdf.set_xy(18, current_y)
            self.pdf.set_fill_color(255, 249, 196)  # Pale yellow caption box
            self.pdf.set_draw_color(80, 80, 80)
            self.pdf.set_font("Helvetica", "B", 10)
            self.pdf.set_text_color(30, 30, 30)
            self.pdf.multi_cell(174, 6, f"CAPTION: {caption.upper()}", border=1, fill=True, align="L")
            current_y = self.pdf.get_y() + 4

        # Dialogue & Narration box
        if dialogue or narration:
            self.pdf.set_xy(18, current_y)
            self.pdf.set_fill_color(250, 250, 252)
            self.pdf.set_draw_color(180, 180, 180)

            content_text = ""
            if dialogue:
                content_text += f"DIALOGUE:\n{dialogue}\n\n"
            if narration:
                content_text += f"NARRATION:\n{narration}"

            self.pdf.set_font("Helvetica", "", 10)
            self.pdf.set_text_color(20, 20, 20)
            self.pdf.multi_cell(174, 5.5, content_text.strip(), border=1, fill=True, align="L")


def save_pdf(
    layout_data: List[Dict[str, Any]],
    story_title: str = "Comic Story",
    character_name: str = "Hero",
    setting: str = "Enchanted Forest",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> Tuple[str, str]:
    """Compiles the full comic into a multi-page PDF using FPDF and saves to static/exports.

    Args:
        layout_data: List of panel layout dictionaries.
        story_title: Title of the comic.
        character_name: Name of the main character.
        setting: Story location.
        tone: Emotional tone.
        art_style: Visual art style.

    Returns:
        Tuple of (web_url, absolute_file_path)
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    clean_title = "".join(c for c in story_title if c.isalnum() or c in (" ", "_")).replace(" ", "_")[:25]
    filename = f"comic_{clean_title}_{ts}.pdf"
    output_path = EXPORTS_DIR / filename
    web_url = f"/static/exports/{filename}"

    builder = ComicPDF(title=story_title)
    builder.add_cover_page(character_name, setting, tone, art_style)

    for panel in layout_data:
        builder.add_panel_page(panel)

    builder.pdf.output(str(output_path))
    logger.info("Exported comic PDF to: %s", output_path)

    return web_url, str(output_path)
