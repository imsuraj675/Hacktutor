# create_video.py
# -*- coding: utf-8 -*-
"""
End-to-end slide video generator wired to YOUR generators:

- generate_audio(text) -> base64 MP3 string
- generate_image(text) -> {"text": <caption/alt>, "image": <base64 image>}

Flow:
1) Plan slides with Gemini (strict JSON schema; API key from .env)
2) For each slide, call generate_image()/generate_audio()
3) Decode base64 to files and assemble with MoviePy

Reqs:
  pip install google-genai moviepy python-dotenv pydantic

.env:
  API_KEY=YOUR_GEMINI_DEVELOPER_API_KEY
"""

from __future__ import annotations
from utils import generate_audio
from gemini_mermaid_api import generate_mermaid_image
import os
import io
import json
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

# Gemini SDK
from google import genai
from google.genai import types as gtypes

# MoviePy
from pathlib import Path
from moviepy import ImageClip, ColorClip, vfx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, concatenate_videoclips


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("create-video")


# ----------------------------------------------------------------------
# Models (strict validation)
# ----------------------------------------------------------------------
class Slide(BaseModel):
    index: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=60)
    narration_text: str = Field(min_length=3)
    image_description: str = Field(min_length=10)

class PlanMeta(BaseModel):
    topic: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    slide_count: Optional[int] = None

class SlidePlan(BaseModel):
    slides: List[Slide]
    meta: Optional[PlanMeta] = None

    @field_validator("slides")
    @classmethod
    def _validate_slides(cls, v: List[Slide]) -> List[Slide]:
        if not v:
            raise ValueError("slides must be non-empty")
        idxs = [s.index for s in v]
        if len(idxs) != len(set(idxs)):
            raise ValueError("slide indexes must be unique")
        return sorted(v, key=lambda s: s.index)


# ----------------------------------------------------------------------
# Structured output schema & prompt
# ----------------------------------------------------------------------
def _schema_for_gemini() -> Dict[str, Any]:
    return {
        "type": "OBJECT",
        "required": ["slides", "meta"],
        "properties": {
            "slides": {
                "type": "ARRAY",
                "minItems": 3,
                "items": {
                    "type": "OBJECT",
                    "required": ["index", "title", "narration_text", "image_description"],
                    "properties": {
                        "index": {"type": "INTEGER"},
                        "title": {"type": "STRING"},
                        "narration_text": {"type": "STRING"},
                        "image_description": {"type": "STRING"}
                    }
                }
            },
            "meta": {
                "type": "OBJECT",
                "properties": {
                    "topic": {"type": "STRING"},
                    "target_audience": {"type": "STRING"},
                    "tone": {"type": "STRING"},
                    "slide_count": {"type": "INTEGER"}
                }
            }
        }
    }

def _build_planning_prompt(user_prompt: str,
                           target_audience="general learners",
                           tone="friendly and concise",
                           slide_min=3,
                           slide_max=5,
                           style_hint="consistent flat vector illustration, no on-image text, aspect ratio 16:9") -> str:
    return f"""
SYSTEM:
You are an instructional slide planner. Return ONLY JSON (no markdown, no explanations) matching the provided schema.

USER:
Create a slide-by-slide plan to teach the topic below.

Constraints:
- {slide_min}–{slide_max} slides total (aim 4).
- Each slide must have:
  • narration_text: 1–3 short sentences, clear, speakable.
  • image_description: Output Mermaid only (no prose/fences). For a 16:9 educational slide on topic, draw a compact left-to-right diagram that shows action feeding the main process. Use `flowchart LR` with ≤3 vertical tiers and 5–7 node labels (≤3 words). Keep a minimalist, high-contrast schematic style; neutral base + one accent; no textures, logos/watermarks, or public figures. Start with this init block exactly, then your diagram:

%%{{init: {{"theme":"base","themeVariables":{{"background":"transparent","fontSize":"20px","lineColor":"#cbd5e1","primaryColor":"#1f2937","primaryTextColor":"#ffffff"}}, "flowchart":{{"useMaxWidth": true}}}}}}%%
flowchart LR
- Flow: intro → key ideas → example(s) → recap.

Audience: {target_audience}
Tone: {tone}
Global visual style hint: {style_hint}

Topic:
\"\"\"{user_prompt}\"\"\"

Output format: application/json ONLY with keys slides[] and meta{{}} as per schema. No extra keys or commentary.
"""


# ----------------------------------------------------------------------
# Gemini client (API key from .env)
# ----------------------------------------------------------------------
def _gemini() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("Missing API_KEY in .env")
    return genai.Client(api_key=api_key)


def _plan_slides_with_gemini(user_prompt: str, model="gemini-2.5-flash") -> SlidePlan:
    client = _gemini()
    schema = _schema_for_gemini()
    prompt = _build_planning_prompt(user_prompt)

    log.info("Requesting slide plan from Gemini (structured JSON)...")
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=gtypes.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.7,
        ),
    )
    raw = resp.parsed if hasattr(resp, "parsed") and resp.parsed else json.loads(resp.text)
    try:
        plan = SlidePlan.model_validate(raw)
    except ValidationError as e:
        # Minimal repair attempt
        if isinstance(raw, dict) and "slides" in raw:
            plan = SlidePlan.model_validate({"slides": raw["slides"], "meta": raw.get("meta", {})})
        else:
            raise RuntimeError(f"Gemini returned invalid JSON: {e}") from e
    return plan


# ----------------------------------------------------------------------
# Base64 helpers (persist media to files for MoviePy)
# ----------------------------------------------------------------------
def _sniff_image_ext(b: bytes) -> str:
    # PNG: 89 50 4E 47, JPG: FF D8 FF, WEBP: "RIFF....WEBP"
    if len(b) >= 4 and b[:4] == b"\x89PNG":
        return ".png"
    if len(b) >= 3 and b[:3] == b"\xFF\xD8\xFF":
        return ".jpg"
    if len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return ".webp"
    return ".png"  # safe default

def _write_b64_to_file(b64: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path

def _save_audio_base64(b64_audio: str, out_dir: Path, index: int) -> Path:
    # gTTS produces MP3 bytes → save as .mp3
    p = out_dir / f"slide_{index:02d}.mp3"
    return _write_b64_to_file(b64_audio, p)

def _save_image_base64(b64_image: str, out_dir: Path, index: int) -> Path:
    # raw = base64.b64decode(b64_image)
    ext = _sniff_image_ext(b64_image)
    p = out_dir / f"slide_{index:02d}{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        f.write(b64_image)
    return p


# ----------------------------------------------------------------------
# Clip assembly
# ----------------------------------------------------------------------
def _build_slide_clip(image_path: Path,
                      audio_path: Path,
                      zoom_strength: float = 0.02,
                      fade: float = 0.25,
                      width: int = 1920,
                      height: int = 1080,
                      fps: int = 30):
    # audio + duration
    aclip = AudioFileClip(str(audio_path))
    dur = max(0.05, float(getattr(aclip, "duration", 0.0) or 0.0))

    # base image
    base = ImageClip(str(image_path))
    iw, ih = base.w, base.h

    # fit-to-canvas (letterbox)
    scale = min(width / iw, height / ih)
    iclip = base.resized(new_size=(int(iw * scale), int(ih * scale))) \
                .with_duration(dur) \
                .with_audio(aclip)

    # optional Ken Burns–style slow zoom
    if zoom_strength:
        iclip = iclip.with_effects([
            vfx.Resize(lambda t: 1.0 + zoom_strength * (t / dur))
        ])

    # fades
    iclip = iclip.with_effects([vfx.FadeIn(fade), vfx.FadeOut(fade)])

    # center on black canvas
    bg = ColorClip(size=(width, height), color=(0, 0, 0)).with_duration(dur)
    comp = CompositeVideoClip([bg, iclip.with_position(("center", "center"))]) \
            .with_fps(fps)
    return comp


def _assemble_video(slide_media: list[tuple[Path, Path]],
                    out_path: Path,
                    fps: int = 30) -> Path:
    clips = []
    for img, aud in slide_media:
        clips.append(_build_slide_clip(img, aud, fps=fps))

    # Import path is key in v2
    final = concatenate_videoclips(clips, method="compose")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(str(out_path), fps=fps, codec="libx264", audio_codec="aac", preset="medium")
    # (Optional) free resources
    for c in clips:
        c.close()
    final.close()
    return out_path


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def createVideo(topic_prompt: str,
                out_path: str = "video.mp4",
                model: str = "gemini-2.5-flash",
                workdir: str = "artifacts") -> str:
    """
    - Plans slides with Gemini
    - Calls your generate_image()/generate_audio() per slide
    - Decodes base64 payloads to files
    - Assembles the final video

    Returns: output video path
    """
    plan = _plan_slides_with_gemini(topic_prompt, model=model)
    slides = plan.slides

    wd = Path(workdir)
    img_dir = wd / "images"
    aud_dir = wd / "audio"
    media_for_assembly: List[Tuple[Path, Path]] = []

    for s in slides:
        # If aspect ratio mention is missing, append it softly (helps consistency)
        desc = s.image_description
        if "aspect ratio" not in desc.lower():
            desc += " ; aspect ratio 16:9"

        # --- IMAGE ---
        img_resp = generate_mermaid_image(desc,theme="neutral")                  # png stream
        img_path = _save_image_base64(img_resp, img_dir, s.index)

        # --- AUDIO ---
        aud_b64 = generate_audio(s.narration_text)       # base64 MP3
        if not isinstance(aud_b64, str):
            raise RuntimeError(f"generate_audio returned invalid payload for slide {s.index}")
        aud_path = _save_audio_base64(aud_b64, aud_dir, s.index)

        media_for_assembly.append((img_path, aud_path))
        log.info(f"Slide {s.index}: saved image -> {img_path.name}, audio -> {aud_path.name}")

    out = _assemble_video(media_for_assembly, Path(out_path))
    log.info(f"Video written to: {out}")
    return str(out)


# ----------------------------------------------------------------------
# Example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    topic = "Introduction to Sorting Algorithms: why sorting matters, big-O intuition, stable vs unstable, and a demo."
    createVideo(topic, out_path="sorting_lesson.mp4")
