import json
import logging
import os
import re
from typing import Any, Dict, List
from app.config import settings

logger = logging.getLogger(__name__)


def _build_fallback_outline(
    story_prompt: str,
    character_name: str = "Hero",
    setting: str = "Enchanted Forest",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> List[Dict[str, Any]]:
    """Generates a rich, creative 5-panel fallback outline when API key is unavailable."""
    return [
        {
            "panel_number": 1,
            "title": f"The Call of the {setting.title()}",
            "scene_description": (
                f"{character_name} stands at the threshold of the {setting}, gaze fixed upon the enigmatic path ahead. "
                f"The atmosphere carries a {tone.lower()} tension as destiny beckons."
            ),
            "image_prompt": (
                f"Wide cinematic comic panel of {character_name} entering the mysterious {setting}, "
                f"{art_style} style, dramatic lighting, detailed background, dynamic angle, bold comic ink outlines"
            )
        },
        {
            "panel_number": 2,
            "title": "A Hidden Discovery",
            "scene_description": (
                f"Venturing deeper into {setting}, {character_name} discovers a glowing ancient artifact pulsing with energy, "
                f"casting eerie shadows across the environment."
            ),
            "image_prompt": (
                f"Medium close-up comic panel of {character_name} inspecting a glowing magical artifact in {setting}, "
                f"{art_style} style, vibrant luminous highlights, expressive facial detail, comic book framing"
            )
        },
        {
            "panel_number": 3,
            "title": "The Looming Threat",
            "scene_description": (
                f"Suddenly, the shadows shift. An ominous guardian awakens from the depths of {setting}, "
                f"challenging {character_name}'s intrusion with immense power."
            ),
            "image_prompt": (
                f"Dynamic action comic panel, towering silhouette guardian confronting {character_name} in {setting}, "
                f"{tone.lower()} mood, {art_style} style, speed lines, high contrast chiaroscuro"
            )
        },
        {
            "panel_number": 4,
            "title": "Clash of Will and Might",
            "scene_description": (
                f"{character_name} stands firm, channeling courage to counter the guardian's attack in a dazzling burst of energy and resolve."
            ),
            "image_prompt": (
                f"Climactic action comic panel, {character_name} unleashing vibrant heroic power against adversary, "
                f"spectacular particle effects, {art_style} illustration, cinematic depth"
            )
        },
        {
            "panel_number": 5,
            "title": "A New Dawn Awakens",
            "scene_description": (
                f"The trial overcome, harmony returns to {setting}. {character_name} looks toward the horizon, transformed by the quest."
            ),
            "image_prompt": (
                f"Inspiring conclusion comic panel, {character_name} standing triumphantly against a radiant sunrise over {setting}, "
                f"peaceful and triumphant, {art_style} style, gorgeous comic art finish"
            )
        }
    ]


def generate_outline(
    story_prompt: str,
    character_name: str = "Hero",
    setting: str = "Enchanted Forest",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> List[Dict[str, Any]]:
    """Generates a structured 5-panel comic outline using Gemini Flash.

    Args:
        story_prompt: The main premise or story idea provided by the user.
        character_name: Name of the protagonist.
        setting: Location/environment.
        tone: Emotional mood or tone.
        art_style: Visual art style for prompt engineering.

    Returns:
        List of 5 dictionaries containing panel_number, title, scene_description, image_prompt.
    """
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        logger.info("No GEMINI_API_KEY found. Generating high-quality creative outline fallback.")
        return _build_fallback_outline(story_prompt, character_name, setting, tone, art_style)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        candidate_models = [
            settings.DEFAULT_MODEL_FLASH,
            "models/gemini-3.8-flash",
            "models/gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-1.5-flash"
        ]

        # Deduplicate while preserving order
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        system_instruction = (
            "You are a professional comic book writer and storyboard artist. "
            "Your task is to produce a compelling, coherent 5-panel comic strip outline based on user specifications. "
            "You MUST respond ONLY with a raw JSON array of exactly 5 panel objects. Do NOT include markdown code blocks or extra text.\n"
            "Each object MUST contain the following keys:\n"
            "- panel_number (integer, 1 to 5)\n"
            "- title (string, short punchy title for the panel)\n"
            "- scene_description (string, 1-2 atmospheric sentences describing the scene, character actions, and mood)\n"
            "- image_prompt (string, detailed descriptive visual prompt for Stable Diffusion, specifying subject, setting, art style, lighting, and camera angle)\n"
        )

        user_content = (
            f"Story Prompt: {story_prompt}\n"
            f"Main Character: {character_name}\n"
            f"Setting: {setting}\n"
            f"Tone: {tone}\n"
            f"Art Style: {art_style}\n"
            "Please create the 5-panel comic outline now in strict JSON format."
        )

        response = None
        for model_name in unique_models:
            try:
                logger.info("Attempting outline generation with Gemini model: %s", model_name)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    f"{system_instruction}\n\n{user_content}",
                    generation_config={"temperature": 0.7, "max_output_tokens": 1500}
                )
                if response and response.text:
                    logger.info("Successfully received outline from Gemini model: %s", model_name)
                    break
            except Exception as model_err:
                logger.warning("Gemini model %s failed: %s", model_name, model_err)

        if response and response.text:
            raw_text = response.text.strip()
            # Clean markdown code block if present
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
            clean_text = re.sub(r"```$", "", clean_text, flags=re.MULTILINE).strip()

            data = json.loads(clean_text)
            if isinstance(data, list) and len(data) >= 1:
                # Ensure proper schema
                normalized = []
                for i, p in enumerate(data[:5], start=1):
                    normalized.append({
                        "panel_number": int(p.get("panel_number", i)),
                        "title": str(p.get("title", f"Panel {i}")),
                        "scene_description": str(p.get("scene_description", "")),
                        "image_prompt": str(p.get("image_prompt", f"{story_prompt}, {art_style} style"))
                    })
                return normalized

    except Exception as exc:
        logger.warning("Gemini Flash outline generation encountered an issue: %s. Using creative fallback.", exc)

    return _build_fallback_outline(story_prompt, character_name, setting, tone, art_style)
