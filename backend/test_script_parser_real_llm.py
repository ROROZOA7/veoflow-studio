"""
Integration tests for ScriptGenerator using the real LLM.
These tests call the configured AI provider (Gemini / OpenAI / Anthropic)
and verify that the JSON response is parsed correctly end-to-end.
"""

import os
from typing import Dict, Any

import pytest

from app.services.script_generator import ScriptGenerator


def _has_any_api_key() -> bool:
  """Return True if at least one supported provider has an API key set."""
  return any(
      bool(os.getenv(env_key))
      for env_key in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
  )


@pytest.mark.asyncio
async def test_generate_script_from_parameters_real_llm() -> None:
  """
  Call the real LLM via ScriptGenerator.generate_script_from_parameters
  and ensure the response is parsed into a valid script structure.
  """
  if not _has_any_api_key():
      pytest.skip(
          "No AI API key configured (GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY). "
          "Skipping real LLM integration test."
      )

  generator = ScriptGenerator()
  if not generator.api_key:
      pytest.skip(
          f"No API key configured for provider {generator.provider}. "
          "Check veoflow.config.json and your environment variables."
      )

  # Use a small example to keep token usage reasonable
  main_content = "The story about a black cat named Pip who learns to make friends."
  video_duration = 64  # total seconds; should produce ~8 scenes of ~8s

  # Call the real LLM. If external quota/rate limits are hit, skip instead of failing.
  try:
      result: Dict[str, Any] = await generator.generate_script_from_parameters(
          main_content=main_content,
          video_duration=video_duration,
          style="cartoon",
          target_audience="children",
          aspect_ratio="16:9",
          language="en-US",
          voice_style="narrator",
          music_style="upbeat",
      )
  except Exception as exc:  # pragma: no cover - defensive guard for external service issues
      message = str(exc).lower()
      if "quota" in message or "rate limit" in message or "429" in message:
          pytest.skip(f"Real LLM test skipped due to external quota/rate limit: {exc}")
      raise

  # --- Debug output: show raw text and parsed structure (visible with `-s`) ---
  print("\n===== RAW FULL SCRIPT TEXT (truncated) =====")
  text_preview = result["text"][:2000]
  print(text_preview)
  if len(result["text"]) > len(text_preview):
      print("\n... [truncated] ...\n")

  print("===== PARSED STORY STRUCTURE =====")
  print(result["story_structure"])

  print("===== PARSED SCENES SUMMARY =====")
  for scene in result["scenes"]:
      num = scene.get("scene_number") or scene.get("number")
      desc = scene.get("description", "") or scene.get("scene_description", "")
      dur = scene.get("duration_sec", 0)
      print(f"Scene {num}: duration={dur}s, desc={desc[:120]}")

  # Basic structure
  assert "text" in result
  assert "scenes" in result
  assert "characters" in result
  assert "story_structure" in result

  scenes = result["scenes"]
  story_structure = result["story_structure"]

  # We should have at least one scene
  assert isinstance(scenes, list)
  assert len(scenes) > 0

  # Each scene should have required fields and a duration
  for scene in scenes:
      assert "scene_number" in scene or "number" in scene
      assert "duration_sec" in scene
      assert isinstance(scene["duration_sec"], int)
      assert scene["duration_sec"] > 0

  # Scene durations should sum to the requested total
  total_duration = sum(scene.get("duration_sec", 0) for scene in scenes)
  assert total_duration == video_duration

  # Story structure should have beginning/middle/end keys
  assert "beginning" in story_structure
  assert "middle" in story_structure
  assert "end" in story_structure

  # Full script text should contain at least one scene marker
  assert "[SCENE " in result["text"]


