import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_comic_layout(
    outline: List[Dict[str, Any]],
    story_panels: List[Dict[str, Any]],
    image_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Organizes generated outlines, narrative scripts, and panel illustrations into a unified layout.

    Args:
        outline: List of panel outline dictionaries from gemini_flash (title, scene_description, image_prompt).
        story_panels: List of story script dictionaries from gemini_pro (caption, narration, dialogue).
        image_data: List of image results [{'panel_number': int, 'image_url': str, 'image_path': str}].

    Returns:
        A list of unified panel layout dictionaries ready for Jinja2 template rendering and PDF export.
    """
    layout: List[Dict[str, Any]] = []

    # Map story panels by panel_number
    story_map = {p.get("panel_number", i + 1): p for i, p in enumerate(story_panels)}
    # Map image data by panel_number
    img_map = {im.get("panel_number", i + 1): im for i, im in enumerate(image_data)}

    for idx, panel in enumerate(outline, start=1):
        p_num = panel.get("panel_number", idx)
        s_item = story_map.get(p_num, {})
        i_item = img_map.get(p_num, {})

        title = panel.get("title") or f"Panel {p_num}"
        scene_desc = panel.get("scene_description", "")
        img_prompt = panel.get("image_prompt", "")

        caption = s_item.get("caption") or f"PANEL {p_num}"
        narration = s_item.get("narration") or ""
        dialogue = s_item.get("dialogue") or ""
        full_text = s_item.get("full_text") or f"{caption}\n\n{dialogue}\n\n{narration}".strip()

        img_url = i_item.get("image_url", "")
        img_path = i_item.get("image_path", "")

        layout.append({
            "panel_number": p_num,
            "title": title,
            "scene_description": scene_desc,
            "caption": caption,
            "narration": narration,
            "dialogue": dialogue,
            "full_text": full_text,
            "image_url": img_url,
            "image_path": img_path,
            "image_prompt": img_prompt
        })

    logger.info("Successfully assembled comic layout with %d panels.", len(layout))
    return layout
