import logging
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import EXPORTS_DIR, TEMPLATES_DIR, settings
from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.models.schemas import (
    ComicResponse,
    ImageTestRequest,
    ImageTestResponse,
    PanelDetail,
    PromptRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the ComicCraft homepage form."""
    has_gemini = bool(settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY"))
    has_hf = bool(settings.HF_API_KEY or os.environ.get("HF_API_KEY"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "default_tone": "Dramatic",
            "default_style": "Comic Book",
            "default_setting": "Enchanted Forest",
            "has_gemini": has_gemini,
            "has_hf": has_hf,
            "image_backend": settings.IMAGE_GEN_BACKEND
        }
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("Enchanted Forest"),
    tone: str = Form("Dramatic"),
    art_style: str = Form("Comic Book")
):
    """Processes HTML form submission, executes AI pipeline, and renders comic_preview.html."""
    try:
        story_prompt = story_prompt.strip()
        character_name = character_name.strip() or "Hero"
        setting = setting.strip() or "Enchanted Forest"
        tone = tone.strip() or "Dramatic"
        art_style = art_style.strip() or "Comic Book"

        logger.info("Starting comic generation for '%s' featuring '%s'", story_prompt[:30], character_name)

        # 1. Generate 5-Panel Outline via Gemini Flash
        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # 2. Generate Detailed Story Scripts (Dialogues, Narration, Captions) via Gemini Pro
        story_panels = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=tone
        )

        # 3. Generate Illustrations for all panels via Image Generator (Diffusers / SD / Canvas)
        image_data = []
        for panel in outline:
            p_num = panel.get("panel_number", 1)
            img_prompt = panel.get("image_prompt", story_prompt)
            img_url, img_path = generate_image(
                prompt=img_prompt,
                panel_number=p_num,
                art_style=art_style
            )
            image_data.append({
                "panel_number": p_num,
                "image_url": img_url,
                "image_path": img_path
            })

        # 4. Assemble Unified Layout
        layout = build_comic_layout(outline, story_panels, image_data)

        # Derive a punchy story title
        story_title = outline[0].get("title", f"The Chronicles of {character_name}")

        # 5. Export Comic to Multi-Page PDF
        pdf_url, pdf_path = save_pdf(
            layout_data=layout,
            story_title=story_title,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )
        pdf_filename = Path(pdf_path).name

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "story_title": story_title,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style,
                "story_prompt": story_prompt,
                "pdf_url": pdf_url,
                "pdf_filename": pdf_filename
            }
        )

    except Exception as exc:
        logger.error("Failed to generate comic: %s", exc, exc_info=True)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_name": settings.APP_NAME,
                "error": f"Error generating comic: {str(exc)}"
            },
            status_code=500
        )


@router.post("/generate-comic/json", response_model=ComicResponse)
async def generate_comic_json(payload: PromptRequest):
    """REST API endpoint to trigger comic generation via JSON payload."""
    try:
        story_prompt = payload.story_prompt.strip()
        character_name = payload.character_name.strip()
        setting = payload.setting.strip()
        tone = payload.tone.strip()
        art_style = payload.art_style.strip()

        # 1. Outline
        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # 2. Story Script
        story_panels = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=tone
        )

        # 3. Illustrations
        image_data = []
        for panel in outline:
            p_num = panel.get("panel_number", 1)
            img_prompt = panel.get("image_prompt", story_prompt)
            img_url, img_path = generate_image(
                prompt=img_prompt,
                panel_number=p_num,
                art_style=art_style
            )
            image_data.append({
                "panel_number": p_num,
                "image_url": img_url,
                "image_path": img_path
            })

        # 4. Layout
        layout = build_comic_layout(outline, story_panels, image_data)
        story_title = outline[0].get("title", f"The Legend of {character_name}")

        # 5. PDF Export
        pdf_url, pdf_path = save_pdf(
            layout_data=layout,
            story_title=story_title,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        panels_response = [PanelDetail(**item) for item in layout]

        return ComicResponse(
            success=True,
            story_title=story_title,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
            panels=panels_response,
            pdf_url=pdf_url,
            pdf_path=pdf_path
        )

    except Exception as exc:
        logger.error("API error during comic generation: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf_url: Optional[str] = None,
    title: Optional[str] = "My AI Comic"
):
    """Renders export confirmation success page."""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url or "#",
            "title": title
        }
    )


@router.get("/download-pdf/{filename}")
@router.head("/download-pdf/{filename}")
async def download_pdf(filename: str):
    """Direct file download for compiled comic PDFs."""
    safe_filename = Path(filename).name
    file_path = EXPORTS_DIR / safe_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested comic PDF not found.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=safe_filename
    )


@router.post("/test-image", response_model=ImageTestResponse)
async def test_image_post(req: ImageTestRequest):
    """Tests standalone image generation via POST."""
    try:
        url, local_path = generate_image(
            prompt=req.prompt,
            panel_number=req.panel_number,
            art_style=req.art_style
        )
        return ImageTestResponse(
            success=True,
            image_url=url,
            image_path=local_path,
            prompt=req.prompt,
            art_style=req.art_style
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/test-image")
async def test_image_get(prompt: str = "A brave explorer discovering a glowing relic in an ancient jungle"):
    """Quick GET endpoint to test image generation in the browser."""
    url, local_path = generate_image(prompt=prompt, panel_number=1, art_style="Comic Book")
    return {
        "success": True,
        "image_url": url,
        "image_path": local_path,
        "prompt": prompt
    }


@router.get("/health")
async def health_check():
    """Diagnostic health check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "has_gemini_key": bool(settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")),
        "has_hf_key": bool(settings.HF_API_KEY or os.environ.get("HF_API_KEY")),
        "image_backend": settings.IMAGE_GEN_BACKEND
    }
