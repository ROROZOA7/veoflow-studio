"""
Scene Builder Service - Builds and optimizes scenes for Veo Ultra
"""

import logging
from typing import Dict, List, Any
from app.utils.prompts import (
    optimize_prompt_for_veo_ultra,
    build_scene_prompt_with_characters
)

logger = logging.getLogger(__name__)


class SceneBuilder:
    """Builds and optimizes scenes for Veo Ultra rendering"""
    
    def build_scene_prompts(
        self,
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]] = None,
        cinematic_style: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        Build optimized scene prompts with character consistency
        
        Args:
            scenes: List of scene dictionaries
            characters: List of character dictionaries
            cinematic_style: Cinematic style settings
        
        Returns:
            List of scenes with optimized prompts
        """
        optimized_scenes = []
        
        # Generate character consistency seeds
        character_seeds = []
        if characters:
            from app.utils.prompts import generate_character_consistency_seed
            character_seeds = [
                generate_character_consistency_seed(char)
                for char in characters
            ]
        
        for scene in scenes:
            # Get base prompt
            base_prompt = scene.get("prompt", scene.get("description", ""))
            
            # Optimize for Veo Ultra
            optimized_prompt = optimize_prompt_for_veo_ultra(
                base_prompt,
                cinematic_style,
                characters
            )
            
            # Add character consistency
            final_prompt = build_scene_prompt_with_characters(
                optimized_prompt,
                character_seeds
            )
            
            optimized_scene = {
                **scene,
                "prompt": final_prompt,
                "optimized": True
            }
            
            optimized_scenes.append(optimized_scene)
        
        return optimized_scenes
    
    def extract_characters_from_scene(
        self,
        scene_text: str,
        characters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract which characters appear in a scene"""
        scene_lower = scene_text.lower()
        appearing_chars = []
        
        for char in characters:
            char_name = char.get("name", "").lower()
            if char_name and char_name in scene_lower:
                appearing_chars.append(char)
        
        return appearing_chars

