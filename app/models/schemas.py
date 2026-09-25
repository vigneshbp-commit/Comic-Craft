"""Pydantic schemas and data models for ComicCraft."""
from typing import List, Optional
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Schema for incoming comic creation requests via JSON API."""
    story_prompt: str = Field(
        ...,
        min_length=3,
        description="Core prompt or storyline premise for the comic",
        examples=["A brave cyber fox exploring an enchanted neon forest."]
    )
    character_name: str = Field(
        default="Hero",
        description="Name of the main protagonist",
        examples=["Rusty"]
    )
    setting: str = Field(
        default="Enchanted Forest",
        description="Primary setting or environment",
        examples=["Enchanted Forest"]
    )
    tone: str = Field(
        default="Dramatic",
        description="Mood/tone of the comic",
        examples=["Dramatic"]
    )
    art_style: str = Field(
        default="Comic Book",
        description="Visual illustration style",
        examples=["Comic Book"]
    )


class PanelOutline(BaseModel):
    """Schema for individual panel outline produced by Gemini Flash."""
    panel_number: int = Field(..., ge=1, le=5)
    title: str = Field(..., description="Short title for this panel")
    scene_description: str = Field(..., description="Atmospheric scene description")
    image_prompt: str = Field(..., description="Detailed visual prompt for image generation")


class PanelDetail(BaseModel):
    """Schema for fully fleshed panel with dialogues, captions, and illustrations."""
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str
    image_url: str
    image_path: Optional[str] = None
    caption: str = ""
    narration: str = ""
    dialogue: str = ""


class ComicResponse(BaseModel):
    """Response schema for JSON API comic generation."""
    success: bool = True
    story_title: str
    character_name: str
    setting: str
    tone: str
    art_style: str
    panels: List[PanelDetail]
    pdf_url: str
    pdf_path: str


class ImageTestRequest(BaseModel):
    """Schema for direct image testing."""
    prompt: str = Field(..., min_length=3)
    panel_number: int = Field(default=1, ge=1, le=10)
    art_style: str = Field(default="Comic Book")


class ImageTestResponse(BaseModel):
    """Response schema for image testing."""
    success: bool = True
    image_url: str
    image_path: str
    prompt: str
    art_style: str
