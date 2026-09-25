import json
import logging
import os
import re
from typing import Any, Dict, List
from app.config import settings

logger = logging.getLogger(__name__)


def _build_fallback_story(
    outline: List[Dict[str, Any]],
    character_name: str = "Hero",
    setting: str = "Enchanted Forest",
    tone: str = "Dramatic"
) -> List[Dict[str, Any]]:
    """Builds vivid, high-stakes comic story narration and dialogues when API key is unavailable."""
    templates = [
        {
            "caption": f"CHAPTER ONE: THE THRESHOLD OF {setting.upper()}",
            "dialogue": f'{character_name}: "No turning back now. Whatever lies ahead... I will face it."',
            "narration": f"The eerie silence of the {setting} presses against {character_name}. With steady footsteps, the journey into the unknown begins."
        },
        {
            "caption": "A SUDDEN FLASH OF LIGHT...",
            "dialogue": f'{character_name}: "Incredible... It has been waiting here for centuries!"',
            "narration": f"Beneath the tangled canopy, an ancient crystalline glow illuminates {character_name}'s astonished face, revealing cryptic runes of old."
        },
        {
            "caption": "DANGER AWAKENS FROM THE SHADOWS!",
            "dialogue": f'Guardian: "None shall trespass upon the sanctum of the forgotten!"\n{character_name}: "I did not come to destroy—stand down!"',
            "narration": f"The ground tremors violently as an imposing sentinel materializes, glowing eyes locked onto {character_name} with furious resolve."
        },
        {
            "caption": "THE CLASH OF DESTINIES!",
            "dialogue": f'{character_name}: "I will not yield!"',
            "narration": f"Energy surges in a brilliant crescent arc as {character_name} counters the onslaught, sparks illuminating the depths of {setting}."
        },
        {
            "caption": "THE DAWN OF A NEW ERA",
            "dialogue": f'{character_name}: "The balance is restored. The realm is safe once more."',
            "narration": f"As the golden morning sun pierces through the mist, {character_name} stands victorious, ready for the next adventure."
        }
    ]

    enriched = []
    for i, panel in enumerate(outline):
        t = templates[i % len(templates)]
        enriched.append({
            "panel_number": panel.get("panel_number", i + 1),
            "caption": t["caption"],
            "dialogue": t["dialogue"],
            "narration": t["narration"],
            "full_text": f"{t['caption']}\n\n{t['dialogue']}\n\n{t['narration']}"
        })
    return enriched


def generate_story(
    outline: List[Dict[str, Any]],
    character_name: str = "Hero",
    setting: str = "Enchanted Forest",
    tone: str = "Dramatic"
) -> List[Dict[str, Any]]:
    """Generates detailed narration and character dialogues for each panel using Gemini Pro.

    Args:
        outline: The 5-panel outline list from gemini_flash.
        character_name: Name of the protagonist.
        setting: Location/setting of the comic.
        tone: Emotional tone of the story.

    Returns:
        List of dictionaries with panel_number, caption, dialogue, narration, full_text.
    """
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        logger.info("No GEMINI_API_KEY found. Generating rich comic story narration fallback.")
        return _build_fallback_story(outline, character_name, setting, tone)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        candidate_models = [
            settings.DEFAULT_MODEL_PRO,
            "models/gemini-3.8-flash",
            "models/gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]
        unique_models = list(dict.fromkeys([m for m in candidate_models if m]))

        system_instruction = (
            "You are a master comic book scriptwriter. Expand the given 5-panel comic outline into an immersive, "
            "vibrant comic script with character dialogue, atmospheric narration, and comic box captions.\n"
            "You MUST respond ONLY with a raw JSON array of objects corresponding to each panel. No markdown code blocks.\n"
            "Each object MUST contain the following keys:\n"
            "- panel_number (integer 1-5)\n"
            "- caption (string, short uppercase comic caption box text, e.g. 'MEANWHILE...' or 'DEEP IN THE CANOPY...')\n"
            "- dialogue (string, character speech lines with speaker names, e.g. 'Rusty: \"Look at that!\"')\n"
            "- narration (string, 1-3 sentences of action narration and emotional depth)\n"
        )

        outline_summary = json.dumps(outline, indent=2)
        prompt = (
            f"Protagonist: {character_name}\n"
            f"Setting: {setting}\n"
            f"Tone: {tone}\n"
            f"Comic Panels Outline:\n{outline_summary}\n\n"
            "Generate the script in strict JSON array format now."
        )

        response = None
        for model_name in unique_models:
            try:
                logger.info("Attempting story generation with Gemini model: %s", model_name)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    f"{system_instruction}\n\n{prompt}",
                    generation_config={"temperature": 0.75, "max_output_tokens": 2048}
                )
                if response and response.text:
                    logger.info("Successfully received story script from Gemini model: %s", model_name)
                    break
            except Exception as model_err:
                logger.warning("Gemini model %s failed: %s", model_name, model_err)

        if response and response.text:
            raw_text = response.text.strip()
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
            clean_text = re.sub(r"```$", "", clean_text, flags=re.MULTILINE).strip()

            data = json.loads(clean_text)
            if isinstance(data, list) and len(data) >= 1:
                result = []
                for i, p in enumerate(data[:len(outline)], start=1):
                    caption = str(p.get("caption", f"PANEL {i}")).strip()
                    dialogue = str(p.get("dialogue", "")).strip()
                    narration = str(p.get("narration", "")).strip()
                    full_text = f"{caption}\n\n{dialogue}\n\n{narration}".strip()
                    result.append({
                        "panel_number": int(p.get("panel_number", i)),
                        "caption": caption,
                        "dialogue": dialogue,
                        "narration": narration,
                        "full_text": full_text
                    })
                return result

    except Exception as exc:
        logger.warning("Gemini Pro story generation encountered an issue: %s. Using creative fallback.", exc)

    return _build_fallback_story(outline, character_name, setting, tone)
