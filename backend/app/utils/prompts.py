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
    
    face = character.get('face', {})
    if face.get('shape'):
        parts.append(f"with {face['shape']} face")
    if face.get('eyes'):
        parts.append(f"{face['eyes']} eyes")
    
    hair = character.get('hair', {})
    if hair.get('color') and hair.get('style'):
        parts.append(f"{hair['color']} {hair['style']} hair")
    if hair.get('length'):
        parts.append(f"{hair['length']} length")
    
    clothing = character.get('clothing', {})
    if clothing.get('style') and clothing.get('typicalOutfit'):
        parts.append(f"wearing {clothing['style']} {clothing['typicalOutfit']}")
    
    if character.get('age'):
        parts.append(f"age approximately {character['age']} years")
    
    body = character.get('body', {})
    if body.get('type'):
        parts.append(f"{body['type']} build")
    
    if face.get('distinctiveFeatures'):
        features = ', '.join(face['distinctiveFeatures'])
        parts.append(f"distinctive features: {features}")
    
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

