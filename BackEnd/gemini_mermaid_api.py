# mermaid_gen.py
# -*- coding: utf-8 -*-
"""
Standalone Mermaid image generator for your pipeline.

Public API:
    generate_mermaid_image(description: str, *, model: str | None = None, theme: str = "default") -> bytes

Environment:
    .env with API_KEY=<your Gemini API key>   (falls back to process env if .env missing)

Prereqs:
    pip install -U google-genai python-dotenv
    npm i -g @mermaid-js/mermaid-cli      # provides the 'mmdc' renderer

This file:
  1) Calls Gemini to produce compact Mermaid code (TEXT only).
  2) Auto-heals Mermaid (adds header, strips brittle 'style'/'classDef').
  3) Renders via Mermaid CLI (mmdc) to PNG (transparent).
  4) Returns PNG bytes.

No other project files required.
"""

from __future__ import annotations

import os
import re
import sys
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

# Load .env (if present) and read API_KEY
try:
    from dotenv import load_dotenv
except Exception as _e:
    raise RuntimeError(
        "python-dotenv not installed. Run: pip install python-dotenv"
    ) from _e

# Gemini SDK
try:
    from google import genai
    from google.genai import types as gtypes
except Exception as _e:
    raise RuntimeError(
        "google-genai not installed. Run: pip install google-genai"
    ) from _e


DEFAULT_TEXT_MODEL = "gemini-2.0-flash-lite"  # fast & inexpensive for text→Mermaid


# -------------------------------
# Gemini client
# -------------------------------
def _gemini_client() -> genai.Client:
    load_dotenv()  # safe if .env absent; does nothing
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("Missing API_KEY (set it in .env or environment).")
    return genai.Client(api_key=api_key)


# -------------------------------
# Mermaid extraction & healing
# -------------------------------
_MERMAID_FENCE = re.compile(r"```(?:mermaid)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

def _extract_mermaid(txt: str) -> Optional[str]:
    """
    Extract a Mermaid snippet from free-form text or fenced block; return None if not found.
    - Strips ```mermaid fences if present
    - Locates first header line starting with 'graph ' or 'flowchart '
    """
    if not isinstance(txt, str):
        return None
    s = txt.strip()

    m = _MERMAID_FENCE.search(s)
    if m:
        s = m.group(1).strip()

    lines = [ln.rstrip() for ln in s.splitlines() if ln.strip()]
    if not lines:
        return None

    start = None
    for i, ln in enumerate(lines):
        low = ln.lstrip().lower()
        if low.startswith("graph ") or low.startswith("flowchart "):
            start = i
            break
    if start is None:
        if lines and lines[0].lower().startswith(("graph ", "flowchart ")):
            start = 0
        else:
            return None

    cleaned = "\n".join(lines[start:]).strip()
    return cleaned or None


def _sanitize_mermaid(code: str) -> str:
    """
    Basic auto-heal to improve mmdc success:
      - ensure a header (default 'flowchart TD')
      - drop brittle 'style' and 'classDef' lines
      - strip trailing whitespace
    """
    c = (code or "").strip()
    if not re.match(r"^(graph|flowchart)\s", c, flags=re.IGNORECASE):
        c = "flowchart TD\n" + c

    out_lines = []
    for ln in c.splitlines():
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith("style ") or low.startswith("classdef "):
            # Often fragile across themes/versions; omit by default.
            continue
        out_lines.append(ln.rstrip())

    healed = "\n".join(out_lines).strip()
    return healed or "flowchart TD\nA[Start] --> B[Step] --> C[End]"


# -------------------------------
# Mermaid CLI (mmdc) resolution & render
# -------------------------------
class MermaidCliNotFound(RuntimeError):
    pass

_MMD_HINT = (
    "Mermaid CLI (mmdc) not found.\n"
    "Install with: npm i -g @mermaid-js/mermaid-cli\n"
    "or set MERMAID_BIN to the executable path."
)

def _resolve_mmdc() -> Tuple[str, bool]:
    """
    Locate Mermaid CLI executable.

    Returns:
        (cmd, use_shell) where use_shell=True for Windows .cmd files.

    Strategy:
      - Respect MERMAID_BIN if set.
      - On Windows, try 'mmdc.cmd'/'mmdc' and the common Roaming path.
      - On POSIX, use PATH lookup for 'mmdc'.
    """
    env = os.getenv("MERMAID_BIN")
    if env:
        if shutil.which(env) or Path(env).exists():
            return env, env.lower().endswith(".cmd")
        raise MermaidCliNotFound(_MMD_HINT)

    system = platform.system().lower()
    if system.startswith("win"):
        for cand in ("mmdc.cmd", "mmdc"):
            found = shutil.which(cand)
            if found:
                return found, cand.endswith(".cmd")
        # typical global npm location on Windows (%AppData%\npm\mmdc.cmd)
        guess = Path.home() / "AppData" / "Roaming" / "npm" / "mmdc.cmd"
        if guess.exists():
            return str(guess), True
        raise MermaidCliNotFound(_MMD_HINT)

    # POSIX
    found = shutil.which("mmdc")
    if found:
        return found, False
    raise MermaidCliNotFound(_MMD_HINT)


def _render_mermaid_png(mermaid_code: str, out_path: Path, theme: str = "default") -> bool:
    """
    Render Mermaid -> PNG via mermaid-cli (mmdc).
    Uses a transparent background.

    CLI flags: -i input -o output -t theme -b transparent
    """
    try:
        bin_path, use_shell = _resolve_mmdc()
    except MermaidCliNotFound as e:
        raise RuntimeError(str(e))

    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _run(src: str) -> bool:
        tmpdir: Path | None = None
        try:
            tmpdir = Path(tempfile.mkdtemp(prefix="mmdc_"))
            mmd_file = tmpdir / "diagram.mmd"
            mmd_file.write_text(src, encoding="utf-8")

            if use_shell:
                cmd = f'"{bin_path}" -i "{mmd_file}" -o "{out_path}" -t {theme} -b transparent'
            else:
                cmd = [bin_path, "-i", str(mmd_file), "-o", str(out_path), "-t", theme, "-b", "transparent"]

            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=use_shell)
            if p.returncode != 0:
                print(f"[mmdc] rc={p.returncode}\n{p.stderr}", file=sys.stderr)
                return False
            return out_path.exists() and out_path.stat().st_size > 0
        except FileNotFoundError:
            raise RuntimeError(_MMD_HINT)
        except Exception as ex:
            print(f"[mmdc] error: {ex}", file=sys.stderr)
            return False
        finally:
            if tmpdir and tmpdir.exists():
                try:
                    shutil.rmtree(tmpdir)
                except Exception:
                    pass

    # Try original, then healed, then a tiny fallback
    if _run(mermaid_code):
        return True
    healed = _sanitize_mermaid(mermaid_code)
    if healed != mermaid_code and _run(healed):
        return True
    fallback = "flowchart TD\nA[Start] --> B[Concept] --> C[End]"
    return _run(fallback)


# -------------------------------
# Gemini → Mermaid
# -------------------------------
def _prompt_for_mermaid(description: str) -> str:
    system = (
        "Produce ONLY a valid, compact Mermaid diagram. "
        "Prefer 'flowchart TD' or 'graph LR'. No narrative text. No code fences. "
        "Avoid 'style' or 'classDef' unless essential."
    )
    user = (
        f"Description:\n{description}\n\n"
        "Constraints:\n"
        "- concise nodes/edges with brief labels\n"
        "- small but informative\n"
        "- output Mermaid code only"
    )
    return system + "\n\n" + user


def _generate_mermaid_text(description: str, model: Optional[str] = None) -> str:
    """
    Ask Gemini to produce Mermaid code (TEXT generation).
    """
    client = _gemini_client()
    chosen = model or DEFAULT_TEXT_MODEL
    prompt = _prompt_for_mermaid(description)

    res = client.models.generate_content(
        model=chosen,
        contents=prompt,
        config=gtypes.GenerateContentConfig(response_modalities=["TEXT"]),
    )

    txt = ""
    if res and getattr(res, "candidates", None):
        parts = res.candidates[0].content.parts
        if parts and getattr(parts[0], "text", None):
            txt = parts[0].text

    mer = _extract_mermaid(txt)
    if not mer:
        mer = "flowchart TD\nA[Start] --> B[Idea] --> C[End]"
    return mer


# -------------------------------
# Public: generate image bytes
# -------------------------------
def generate_mermaid_image(description: str,
                           *,
                           model: Optional[str] = None,
                           theme: str = "default") -> bytes:
    """
    Generate a Mermaid diagram image for `description` and return PNG bytes.

    Args:
        description: Natural-language description to turn into a diagram.
        model: Optional Gemini model name (defaults to a fast text model).
        theme: Mermaid CLI theme (default 'default').

    Returns:
        PNG image bytes (transparent background).
    """
    mermaid_code = _generate_mermaid_text(description, model=model)

    with tempfile.TemporaryDirectory(prefix="mermaid_img_") as tmpdir:
        out_path = Path(tmpdir) / "diagram.png"
        ok = _render_mermaid_png(mermaid_code, out_path, theme=theme)
        if not ok:
            raise RuntimeError("Mermaid rendering failed. Ensure mermaid-cli is installed and on PATH.")
        return out_path.read_bytes()


# -------------------------------
# Smoke test (optional)
# -------------------------------
if __name__ == "__main__":
    demo = "Insertion sort: compare, shift, insert; best/avg/worst cases."
    png = generate_mermaid_image(demo, theme="default")
    Path("test_mermaid_output.png").write_bytes(png)
    print("Wrote test_mermaid_output.png (bytes:", len(png), ")")
