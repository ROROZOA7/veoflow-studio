"""
Prompt templates and utilities for Veo Ultra optimization
"""

from typing import Dict, List, Any


def build_story_expansion_prompt(user_prompt: str) -> str:
    """Build prompt for story expansion"""
    return f"""You are a video script writer. Expand the following user request into a detailed story:

User Request: {user_prompt}

Provide:
1. Story Summary (2-3 sentences)
2. Main Characters (names, brief descriptions)
3. Key Scenes (5-10 scenes with brief descriptions)
4. Cinematic Style (camera work, mood, pacing)

Format as JSON:
{{
  "summary": "...",
  "characters": [{{"name": "...", "description": "..."}}],
  "scenes": [{{"number": 1, "description": "...", "duration": "5-10s"}}],
  "cinematicStyle": {{"camera": "...", "mood": "...", "pacing": "..."}}
}}"""


def build_script_generation_prompt(expansion: Dict[str, Any]) -> str:
    """Build prompt for script generation"""
    return f"""Write a detailed video script based on this story breakdown:

Summary: {expansion.get('summary', '')}
Characters: {expansion.get('characters', [])}
Scenes: {expansion.get('scenes', [])}
Style: {expansion.get('cinematicStyle', {})}

Write the script with clear scene markers [SCENE 1], [SCENE 2], etc.
Include dialogue, actions, and camera directions.
Keep each scene concise (5-15 seconds of video)."""


def optimize_prompt_for_veo_ultra(
    scene_description: str,
    cinematic_style: Dict[str, str] = None,
    characters: List[Dict[str, Any]] = None
) -> str:
    """
    Optimize scene prompt for Veo Ultra
    
    Template: [Subject], [Camera Style], [Motion], [Lighting], [Environment], [Actions], [Character Consistency]
    """
    prompt_parts = [scene_description]
    
    if cinematic_style:
        if cinematic_style.get('camera'):
            prompt_parts.append(f"{cinematic_style['camera']} shot")
        if cinematic_style.get('mood'):
            prompt_parts.append(f"{cinematic_style['mood']} mood")
    
    if characters:
        char_names = [char.get('name', '') for char in characters if char.get('name')]
        if char_names:
            prompt_parts.append(f"featuring {', '.join(char_names)}")
    
    return ", ".join(prompt_parts)


def generate_character_consistency_seed(character: Dict[str, Any]) -> str:
    """Generate consistency seed prompt for a character"""
    parts = []
    
    gender = character.get('gender', '')
    if gender:
        parts.append(f"always depict the same {gender} character")
    
    # The character DNA in our DB uses simple string fields like "hair", "face_shape",
    # "body_build", etc. Older JSON templates used nested objects. Be tolerant of both
    # so we don't crash when an LLM returns a simpler structure.
    face = character.get('face', {})
    if isinstance(face, dict):
        if face.get('shape'):
            parts.append(f"with {face['shape']} face")
        if face.get('eyes'):
            parts.append(f"{face['eyes']} eyes")
    face_shape = character.get('face_shape')
    if isinstance(face_shape, str) and face_shape:
        parts.append(f"with {face_shape} face")
    
    hair = character.get('hair', {})
    if isinstance(hair, dict):
        if hair.get('color') and hair.get('style'):
            parts.append(f"{hair['color']} {hair['style']} hair")
        if hair.get('length'):
            parts.append(f"{hair['length']} length")
    elif isinstance(hair, str) and hair:
        parts.append(f"{hair} hair")
    
    clothing = character.get('clothing', {})
    if isinstance(clothing, dict) and clothing.get('style') and clothing.get('typicalOutfit'):
        parts.append(f"wearing {clothing['style']} {clothing['typicalOutfit']}")
    
    if character.get('age'):
        parts.append(f"age approximately {character['age']} years")
    
    body = character.get('body', {})
    if isinstance(body, dict) and body.get('type'):
        parts.append(f"{body['type']} build")
    body_build = character.get('body_build')
    if isinstance(body_build, str) and body_build:
        parts.append(f"{body_build} build")
    
    if isinstance(face, dict) and face.get('distinctiveFeatures'):
        features = ', '.join(face['distinctiveFeatures'])
        parts.append(f"distinctive features: {features}")
    signature_feature = character.get('signature_feature')
    if isinstance(signature_feature, str) and signature_feature:
        parts.append(f"distinctive features: {signature_feature}")
    
    parts.append("consistent across all scenes")
    
    return ", ".join([p for p in parts if p])


def build_scene_prompt_with_characters(
    scene_prompt: str,
    character_seeds: List[str]
) -> str:
    """Build final scene prompt with character consistency seeds"""
    if character_seeds:
        combined_seed = "; ".join(character_seeds)
        return f"{combined_seed}, {scene_prompt}"
    return scene_prompt


def build_script_generation_prompt_from_parameters(
    main_content: str,
    video_duration: int,
    style: str,
    target_audience: str,
    aspect_ratio: str,
    language: str = None,
    voice_style: str = None,
    music_style: str = None,
    color_palette: str = None,
    transition_style: str = None
) -> str:
    """Build script generation prompt with all user parameters"""
    optional_params = []
    if language:
        optional_params.append(f"Language/Locale: {language}")
    if voice_style:
        optional_params.append(f"Voice Style: {voice_style}")
    if music_style:
        optional_params.append(f"Music Style: {music_style}")
    if color_palette:
        optional_params.append(f"Color Palette: {color_palette}")
    if transition_style:
        optional_params.append(f"Scene Transition Style: {transition_style}")
    
    optional_text = "\n".join(optional_params) if optional_params else "None specified"
    
    # Calculate approximate scene count targeting ~8s per scene for Veo3
    avg_scene_duration = 8
    scene_count = max(1, round(video_duration / avg_scene_duration))
    
    return f"""You are a professional video script writer. Generate a complete video script based on the following parameters:

Main Content/Story: {main_content}
Total Video Duration: {video_duration} seconds
Style: {style}
Target Audience: {target_audience}
Aspect Ratio: {aspect_ratio}

Optional Parameters:
{optional_text}

Requirements:
1. Create a story with clear beginning, middle, and end
2. Break down into scenes where:
   - IMPORTANT: Each scene should be approximately 8 seconds long (Veo 3 generates ~8s clips per scene)
   - Number of scenes should be approximately {scene_count} scenes (calculated as: total_duration / 8)
   - Total duration of all scenes must sum to exactly {video_duration} seconds
   - DO NOT create many short scenes (e.g., 3-4 seconds each). Instead, create fewer scenes of ~8 seconds each
   - Each scene should contain enough visual content to fill 8 seconds of video
3. Identify all characters that appear
4. Create scene descriptions with visual details appropriate for:
   - Style: {style}
   - Target Audience: {target_audience}
   - Aspect Ratio: {aspect_ratio} (affects camera framing)
5. Ensure story is appropriate for {target_audience}

Output format: JSON with structure:
{{
  "story_structure": {{
    "beginning": "...",
    "middle": "...",
    "end": "..."
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "description": "...",
      "characters": ["Character Name"],
      "duration_sec": 8,
      "visual_style": "{style}",
      "camera_framing": "adjusted for {aspect_ratio}",
      "environment": "..."
    }}
  ],
  "characters": [
    {{
      "name": "Character Name",
      "role": "...",
      "description": "..."
    }}
  ],
  "total_duration": {video_duration},
  "scene_count": <calculated>
}}

Ensure the scene durations sum to exactly {video_duration} seconds."""


def build_character_dna_prompt(
    character_name: str,
    character_description: str,
    script_context: str,
    style: str,
    target_audience: str
) -> str:
    """Build character DNA generation prompt"""
    return f"""You are a character designer. Create a detailed character design based on the following information:

Character Name: {character_name}
Character Description: {character_description}
Script Context: {script_context}
Style: {style}
Target Audience: {target_audience}

Generate a complete character design following this template:
Note: The character should be designed in {style} style and be appropriate for {target_audience} audience.

{{
  "name": "...",
  "species": "...",
  "gender": "...",
  "age_description": "...",
  "voice_personality": "...",
  "body_build": "...",
  "face_shape": "...",
  "hair": "...",
  "skin_or_fur_color": "...",
  "signature_feature": "...",
  "outfit_top": "...",
  "outfit_bottom": "...",
  "helmet_or_hat": "...",
  "shoes_or_footwear": "...",
  "props": "...",
  "body_metrics": {{
    "unit": "cm",
    "height": ...,
    "head": ...,
    "shoulder": ...,
    "torso": ...,
    "tail": ...,
    "paws": ...
  }}
}}

Ensure the character design is:
- Detailed and specific
- Consistent with the story context
- Suitable for 3D animation
- Visually appealing
- Appropriate for {target_audience} audience
- Styled as {style}"""


def build_scene_prompt_generation_prompt(
    scene_description: str,
    scene_number: int,
    duration_sec: int,
    characters_with_dna: List[Dict[str, Any]],
    environment: str,
    style: str,
    target_audience: str,
    aspect_ratio: str
) -> str:
    """Build scene prompt generation prompt"""
    characters_text = "\n".join([
        f"- {char.get('name', 'Unknown')}: {char.get('description', '')}"
        for char in characters_with_dna
    ])
    
    return f"""You are a video scene director. Create a detailed scene prompt for video generation.

Scene Description: {scene_description}
Scene Number: {scene_number}
Scene Duration: {duration_sec} seconds
Characters in Scene:
{characters_text}
Environment: {environment}
Visual Style: {style}
Target Audience: {target_audience}
Aspect Ratio: {aspect_ratio}

Generate a detailed prompt that includes:
1. Character appearance (from Character DNA, maintaining consistency)
2. Character position, pose, expression (scene-specific)
3. Environment details
4. Camera angle and framing (adjusted for {aspect_ratio} aspect ratio)
5. Lighting and atmosphere
6. Action flow (appropriate for {duration_sec} seconds)
7. Visual style: {style}
8. Content appropriate for {target_audience}

Output: A single, detailed prompt string suitable for video generation that combines all elements.
Ensure the prompt maintains character consistency and fits the {duration_sec} second duration."""

