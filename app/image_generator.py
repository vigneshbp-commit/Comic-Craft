import hashlib
import logging
import math
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from app.config import PANELS_DIR, settings

logger = logging.getLogger(__name__)

# Cache for local diffusers pipeline
_local_pipeline = None


def sanitize_filename(prompt: str, panel_number: int = 1) -> str:
    """Sanitizes prompt into a safe, clean filename for comic panels."""
    clean_words = re.sub(r"[^a-zA-Z0-9\s]", "", prompt).split()
    short_slug = "_".join(clean_words[:5]).lower() if clean_words else "scene"
    ts = int(time.time() * 1000) % 1000000
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:6]
    return f"panel_{panel_number}_{short_slug}_{prompt_hash}_{ts}.png"


def _draw_comic_canvas(
    prompt: str,
    panel_number: int,
    art_style: str = "Comic Book",
    output_path: Path = None,
    width: int = 768,
    height: int = 512
) -> str:
    """Creates a high-resolution, beautifully styled comic illustration using Pillow.

    Includes dynamic gradient backgrounds, comic halftone dot textures, action sunbursts,
    vintage comic border framing, panel badges, and stylized typographic elements.
    """
    img = Image.new("RGBA", (width, height), (20, 24, 33, 255))
    draw = ImageDraw.Draw(img)

    # Style palette selection
    style_key = art_style.lower()
    if "anime" in style_key:
        top_color = (255, 126, 179)
        mid_color = (130, 80, 223)
        bottom_color = (36, 18, 54)
        accent_color = (255, 230, 109)
    elif "pixel" in style_key:
        top_color = (56, 189, 248)
        mid_color = (59, 130, 246)
        bottom_color = (15, 23, 42)
        accent_color = (74, 222, 128)
    elif "noir" in style_key:
        top_color = (100, 100, 100)
        mid_color = (40, 40, 40)
        bottom_color = (10, 10, 10)
        accent_color = (220, 38, 38)
    elif "realistic" in style_key:
        top_color = (74, 85, 104)
        mid_color = (45, 55, 72)
        bottom_color = (26, 32, 44)
        accent_color = (246, 173, 85)
    else:  # Classic Comic Book
        # Panel-based color variety
        palettes = [
            ((255, 94, 98), (255, 153, 102), (30, 20, 45), (255, 225, 53)),    # Panel 1
            ((69, 104, 220), (176, 106, 179), (20, 30, 60), (0, 242, 254)),   # Panel 2
            ((238, 9, 121), (255, 106, 0), (40, 10, 20), (255, 235, 59)),     # Panel 3
            ((78, 84, 200), (143, 148, 251), (15, 15, 45), (255, 87, 34)),    # Panel 4
            ((17, 153, 142), (56, 239, 125), (10, 40, 35), (255, 235, 59)),   # Panel 5
        ]
        top_color, mid_color, bottom_color, accent_color = palettes[(panel_number - 1) % len(palettes)]

    # 1. Background multi-stop vertical gradient
    for y in range(height):
        if y < height // 2:
            factor = y / (height / 2)
            r = int(top_color[0] + (mid_color[0] - top_color[0]) * factor)
            g = int(top_color[1] + (mid_color[1] - top_color[1]) * factor)
            b = int(top_color[2] + (mid_color[2] - top_color[2]) * factor)
        else:
            factor = (y - height / 2) / (height / 2)
            r = int(mid_color[0] + (bottom_color[0] - mid_color[0]) * factor)
            g = int(mid_color[1] + (bottom_color[1] - mid_color[1]) * factor)
            b = int(mid_color[2] + (bottom_color[2] - mid_color[2]) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # 2. Comic Action Sunburst / Radial Rays (Climactic or dynamic feel)
    cx, cy = width // 2, height // 2
    num_rays = 24
    ray_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ray_draw = ImageDraw.Draw(ray_overlay)
    max_radius = math.hypot(width, height)
    angle_step = (2 * math.pi) / num_rays

    for i in range(0, num_rays, 2):
        a1 = i * angle_step
        a2 = (i + 0.8) * angle_step
        p1 = (cx, cy)
        p2 = (cx + max_radius * math.cos(a1), cy + max_radius * math.sin(a1))
        p3 = (cx + max_radius * math.cos(a2), cy + max_radius * math.sin(a2))
        ray_draw.polygon([p1, p2, p3], fill=(255, 255, 255, 22))
    img = Image.alpha_composite(img, ray_overlay)
    draw = ImageDraw.Draw(img)

    # 3. Halftone Dot Texture overlay
    grid_size = 18
    dot_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dot_draw = ImageDraw.Draw(dot_overlay)
    for gx in range(0, width, grid_size):
        for gy in range(0, height, grid_size):
            dist = math.hypot(gx - cx, gy - cy)
            rad = max(1, int(3 * (dist / (width / 1.5))))
            if rad > 0:
                dot_draw.ellipse(
                    [(gx - rad, gy - rad), (gx + rad, gy + rad)],
                    fill=(0, 0, 0, 35)
                )
    img = Image.alpha_composite(img, dot_overlay)
    draw = ImageDraw.Draw(img)

    # 4. Stylized Center Foreground Silhouette / Comic Composition
    ground_y = int(height * 0.72)
    p_lower = prompt.lower()

    # Thematic environmental background silhouettes
    if any(k in p_lower for k in ["steam", "lab", "gear", "factory", "machin"]):
        # Steampunk cogs and pipes
        for gx, gy, rad in [(120, ground_y - 80, 50), (640, ground_y - 100, 65), (200, ground_y - 120, 35)]:
            draw.ellipse([(gx - rad, gy - rad), (gx + rad, gy + rad)], fill=(25, 20, 30, 210), outline=(220, 180, 80, 180), width=4)
            # Gear teeth
            for ga in range(0, 360, 45):
                arad = math.radians(ga)
                tx, ty = gx + (rad + 6) * math.cos(arad), gy + (rad + 6) * math.sin(arad)
                draw.rectangle([(tx - 6, ty - 6), (tx + 6, ty + 6)], fill=(220, 180, 80, 200))
    elif any(k in p_lower for k in ["forest", "tree", "wood", "jungle", "swamp"]):
        # Pine trees silhouette
        for tx in [80, 160, 220, 560, 620, 690]:
            th = 130 + (tx % 50)
            draw.polygon([(tx, ground_y - th), (tx - 30, ground_y), (tx + 30, ground_y)], fill=(12, 28, 20, 240))
    elif any(k in p_lower for k in ["city", "cyber", "urban", "roof", "neon"]):
        # Skyscraper silhouette with lighted windows
        for bx, bw, bh in [(50, 90, 180), (160, 110, 230), (520, 100, 210), (640, 80, 170)]:
            draw.rectangle([(bx, ground_y - bh), (bx + bw, ground_y)], fill=(15, 20, 35, 240), outline=(0, 240, 255, 100), width=2)
            for wx in range(bx + 12, bx + bw - 12, 18):
                for wy in range(ground_y - bh + 20, ground_y - 20, 30):
                    draw.rectangle([(wx, wy), (wx + 8, wy + 14)], fill=(255, 235, 59, 180))
    elif any(k in p_lower for k in ["space", "star", "cosmic", "alien", "orbit"]):
        # Cosmic planet crescent & stars
        draw.ellipse([(600, 50), (720, 170)], fill=(240, 240, 255, 220))
        draw.ellipse([(580, 40), (700, 160)], fill=mid_color)
        for sx, sy in [(100, 80), (180, 140), (280, 70), (450, 110), (520, 60)]:
            draw.text((sx, sy), "✦", fill=(255, 255, 255, 220))

    # Ground terrain
    draw.polygon(
        [(0, ground_y), (width, ground_y - 20), (width, height), (0, height)],
        fill=(15, 17, 26, 255)
    )

    # Dynamic heroic character silhouette in center
    hx, hy = width // 2, ground_y - 10
    head_rad = 22
    # Cape / cloak fluttering to the left
    draw.polygon([(hx - 15, hy - 95), (hx - 90, hy - 30), (hx - 30, hy)], fill=(8, 10, 15, 240))
    # Head & headband/hair spikes
    draw.ellipse(
        [(hx - head_rad, hy - 110 - head_rad), (hx + head_rad, hy - 110 + head_rad)],
        fill=(10, 12, 18, 255)
    )
    # Spiky anime hair / comic cowl
    for spike_angle in [-45, -20, 0, 20, 45]:
        srad = math.radians(spike_angle - 90)
        spx = hx + 32 * math.cos(srad)
        spy = (hy - 110) + 32 * math.sin(srad)
        draw.polygon([(hx - 10, hy - 115), (hx + 10, hy - 115), (spx, spy)], fill=(10, 12, 18, 255))
    # Heroic body / armor stance
    draw.polygon([(hx - 24, hy - 90), (hx + 24, hy - 90), (hx + 30, hy), (hx - 30, hy)], fill=(10, 12, 18, 255))
    # Heroic staff / blade
    draw.line([(hx + 26, hy - 130), (hx + 32, hy)], fill=accent_color, width=4)

    # 5. Bold Comic Panel Border
    border_thick = 10
    draw.rectangle(
        [(border_thick // 2, border_thick // 2), (width - border_thick // 2, height - border_thick // 2)],
        outline=(20, 20, 20, 255),
        width=border_thick
    )
    # Inner border line
    draw.rectangle(
        [(border_thick + 4, border_thick + 4), (width - border_thick - 4, height - border_thick - 4)],
        outline=(255, 255, 255, 140),
        width=2
    )

    # 6. Panel Badge (Upper Left)
    badge_w, badge_h = 160, 40
    bx1, by1 = border_thick + 12, border_thick + 12
    draw.rectangle([(bx1 + 3, by1 + 3), (bx1 + badge_w + 3, by1 + badge_h + 3)], fill=(0, 0, 0, 200))
    draw.rectangle([(bx1, by1), (bx1 + badge_w, by1 + badge_h)], fill=accent_color, outline=(0, 0, 0, 255), width=3)
    badge_text = f"PANEL {panel_number} • {art_style.upper()}"
    draw.text((bx1 + 10, by1 + 10), badge_text[:20], fill=(10, 10, 10, 255))

    # 7. Lower Scene Caption Banner
    bar_h = 56
    bar_y = height - border_thick - bar_h - 10
    draw.rectangle(
        [(border_thick + 14, bar_y + 3), (width - border_thick - 14, bar_y + bar_h + 3)],
        fill=(0, 0, 0, 180)
    )
    draw.rectangle(
        [(border_thick + 10, bar_y), (width - border_thick - 10, bar_y + bar_h)],
        fill=(255, 248, 220, 245),
        outline=(20, 20, 20, 255),
        width=3
    )

    clean_prompt = prompt.replace("\n", " ").strip()
    if len(clean_prompt) > 85:
        clean_prompt = clean_prompt[:82] + "..."
    draw.text(
        (border_thick + 24, bar_y + 14),
        f'"{clean_prompt}"',
        fill=(20, 20, 20, 255)
    )

    # Convert to RGB and save
    final_img = img.convert("RGB")
    final_img.save(output_path, format="PNG", quality=95)
    return str(output_path)


def _generate_with_pollinations(
    prompt: str,
    panel_number: int,
    art_style: str,
    output_path: Path
) -> bool:
    """Generates a real AI illustration using Pollinations AI (Flux / Stable Diffusion).

    Free, zero-config cloud AI generator that generates high quality comic art matching the exact prompt.
    """
    import urllib.parse
    import requests

    enhanced_prompt = (
        f"comic book panel artwork, {art_style} style, {prompt}, "
        f"detailed comic illustration, graphic novel art, sharp vibrant colors, clean ink outlines"
    )
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = (int(time.time() * 1000) + panel_number * 37) % 10000000

    api_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=768&height=512&nologo=true&seed={seed}&enhance=false"
    )

    try:
        logger.info("Generating AI panel #%d image via Pollinations AI: %s", panel_number, prompt[:40])
        response = requests.get(api_url, timeout=getattr(settings, "IMAGE_GEN_TIMEOUT", 45))
        if response.status_code == 200 and len(response.content) > 1024:
            with open(output_path, "wb") as f:
                f.write(response.content)
            # Verify image integrity
            with Image.open(output_path) as img:
                img.verify()
            logger.info("Successfully generated AI panel image with Pollinations: %s", output_path.name)
            return True
        logger.warning("Pollinations responded with status %s", response.status_code)
    except Exception as exc:
        logger.warning("Pollinations AI generation failed: %s. Moving to fallback.", exc)
    return False


def _generate_with_hf_api(prompt: str, api_token: str, output_path: Path) -> bool:
    """Attempts generation via Hugging Face Serverless Inference API."""
    import requests
    headers = {"Authorization": f"Bearer {api_token}"}
    comic_prompt = (
        f"comic book panel illustration, {prompt}, vivid dynamic colors, "
        f"sharp comic ink outlines, masterpiece graphic novel art, high quality"
    )

    model_candidates = [
        settings.SD_MODEL_ID,
        "stabilityai/stable-diffusion-3-medium-diffusers",
        "ByteDance/SDXL-Lightning",
        "stabilityai/sdxl-turbo"
    ]
    unique_models = list(dict.fromkeys([m for m in model_candidates if m]))

    timeout = getattr(settings, "IMAGE_GEN_TIMEOUT", 60)

    for model_id in unique_models:
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        try:
            logger.info("Attempting HF API generation with model: %s", model_id)
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": comic_prompt},
                timeout=timeout
            )
            # If model is loading, wait briefly and retry once
            if response.status_code == 503:
                logger.info("Model %s is loading on HF. Waiting 4s to retry...", model_id)
                time.sleep(4)
                response = requests.post(
                    api_url,
                    headers=headers,
                    json={"inputs": comic_prompt},
                    timeout=timeout
                )

            if response.status_code == 200 and len(response.content) > 1024:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                # Verify image can be opened
                with Image.open(output_path) as img:
                    img.verify()
                logger.info("Successfully generated AI panel image via HF API (%s): %s", model_id, output_path.name)
                return True

            logger.warning("HF API (%s) returned status %s: %s", model_id, response.status_code, response.text[:150])
        except Exception as e:
            logger.warning("HF API call failed for %s: %s", model_id, e)

    return False


def _generate_with_local_diffusers(prompt: str, output_path: Path) -> bool:
    """Attempts generation using local diffusers StableDiffusionPipeline if installed."""
    global _local_pipeline
    try:
        import torch
        from diffusers import StableDiffusionPipeline

        if _local_pipeline is None:
            model_id = settings.SD_MODEL_ID
            logger.info("Loading local Stable Diffusion model: %s", model_id)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            _local_pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                safety_checker=None
            )
            _local_pipeline.to(device)

        comic_prompt = f"comic strip panel art, {prompt}, crisp comic ink lines, vibrant color, detailed"
        image = _local_pipeline(comic_prompt, num_inference_steps=20, guidance_scale=7.5).images[0]
        image.save(output_path)
        return True
    except Exception as e:
        logger.info("Local Diffusers generation unavailable or failed: %s", e)
        return False


def generate_image(prompt: str, panel_number: int = 1, art_style: str = "Comic Book") -> Tuple[str, str]:
    """Generates a comic-style image for a panel and returns (web_url, absolute_path).

    Follows a resilient multi-tier generation pipeline:
    1. Local diffusers pipeline (if backend is 'local').
    2. Hugging Face Inference API (if HF_API_KEY is provided and backend is 'auto' or 'hf_api').
    3. Pollinations Cloud AI (Zero-config, real AI illustration matching the exact prompt).
    4. Procedural Comic Canvas Engine (Pillow offline emergency fallback).

    Args:
        prompt: Scene or image description.
        panel_number: Index of the comic panel (1-5).
        art_style: Preferred artistic style.

    Returns:
        Tuple of (web_url, absolute_file_path)
    """
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(prompt, panel_number)
    output_path = PANELS_DIR / filename
    web_url = f"/static/panels/{filename}"

    backend = (settings.IMAGE_GEN_BACKEND or "auto").lower()
    hf_key = settings.HF_API_KEY or os.environ.get("HF_API_KEY", "")

    # Tier 1: Local Diffusers
    if backend == "local":
        if _generate_with_local_diffusers(prompt, output_path):
            return web_url, str(output_path)

    # Tier 2: HF API (if API key provided or explicitly selected)
    if (backend in ["hf_api", "auto"]) and hf_key:
        if _generate_with_hf_api(prompt, hf_key, output_path):
            return web_url, str(output_path)

    # Tier 3: Zero-Config Cloud AI Synthesis (Pollinations AI)
    if (backend in ["auto", "pollinations"]) and getattr(settings, "POLLINATIONS_ENABLED", True):
        if _generate_with_pollinations(prompt, panel_number, art_style, output_path):
            return web_url, str(output_path)

    # Tier 4: Emergency Procedural Canvas Engine (offline fallback)
    logger.info("Using emergency comic canvas fallback for panel #%d", panel_number)
    _draw_comic_canvas(
        prompt=prompt,
        panel_number=panel_number,
        art_style=art_style,
        output_path=output_path
    )

    return web_url, str(output_path)
