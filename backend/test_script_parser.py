"""
Tests for ScriptGenerator JSON parsing.
These tests are local/unit tests and do NOT call any external AI service.
"""

import pytest

from app.services.script_generator import ScriptGenerator


@pytest.fixture
def generator() -> ScriptGenerator:
    return ScriptGenerator()


def _build_sample_response() -> str:
    """Return a sample JSON response similar to what the LLM should produce."""
    return """
{
  "story_structure": {
    "beginning": "The story about a black cat named Pip in a sunny meadow.",
    "middle": "Pip learns that true friends look beyond appearances.",
    "end": "The meadow animals accept Pip, and they all play together."
  },
  "scenes": [
    {
      "scene_number": 1,
      "description": "Pip the black cat watches other animals playing from a distance.",
      "characters": ["Pip", "Meadow Animals"],
      "duration_sec": 8,
      "visual_style": "cartoon",
      "camera_framing": "wide shot",
      "environment": "sunny meadow"
    },
    {
      "scene_number": 2,
      "description": "Pip bravely approaches the group and offers to help.",
      "characters": ["Pip", "Meadow Animals"],
      "duration_sec": 8,
      "visual_style": "cartoon",
      "camera_framing": "medium shot",
      "environment": "near a big tree in the meadow"
    }
  ],
  "characters": [
    {
      "name": "Pip",
      "role": "main character",
      "description": "A kind black cat who wants to make friends."
    }
  ],
  "total_duration": 120,
  "scene_count": 2
}
""".strip()


def test_parse_script_response_plain_json(generator: ScriptGenerator) -> None:
    """Ensure plain JSON string is parsed correctly."""
    response = _build_sample_response()
    data = generator._parse_script_response(response)  # type: ignore[attr-defined]

    assert "story_structure" in data
    assert "scenes" in data
    assert "characters" in data
    assert len(data["scenes"]) == 2
    assert data["story_structure"]["beginning"].startswith("The story about a black cat")


def test_parse_script_response_with_markdown_fence(generator: ScriptGenerator) -> None:
    """Ensure JSON inside ```json fences is parsed correctly."""
    response = f"Here is your script:\\n```json\\n{_build_sample_response()}\\n```\\n"
    data = generator._parse_script_response(response)  # type: ignore[attr-defined]

    assert "scenes" in data
    assert len(data["scenes"]) == 2
    assert data["scenes"][0]["scene_number"] == 1


def test_parse_script_response_invalid_json_raises(generator: ScriptGenerator) -> None:
    """Ensure invalid JSON raises a clear ValueError."""
    bad_response = '{"story_structure": {"beginning": "Unterminated string...}'  # missing closing quote/braces

    with pytest.raises(ValueError) as exc:
        generator._parse_script_response(bad_response)  # type: ignore[attr-defined]

    assert "Invalid JSON response from AI" in str(exc.value)




