"""
Character Manager Service - Handles character consistency
"""

import logging
from typing import Dict, Any, List
from app.utils.prompts import generate_character_consistency_seed

logger = logging.getLogger(__name__)


class CharacterManager:
    """Manages character consistency across scenes"""
    
    def generate_consistency_seed(self, character: Dict[str, Any]) -> str:
        """
        Generate consistency seed prompt for a character
        
        Args:
            character: Character dictionary with DNA attributes
        
        Returns:
            Consistency seed prompt string
        """
        return generate_character_consistency_seed(character)
    
    def build_scene_prompt_with_characters(
        self,
        scene_prompt: str,
        characters: List[Dict[str, Any]]
    ) -> str:
        """
        Build scene prompt with character consistency seeds
        
        Args:
            scene_prompt: Base scene prompt
            characters: List of characters appearing in scene
        
        Returns:
            Final prompt with character consistency
        """
        if not characters:
            return scene_prompt
        
        character_seeds = [
            self.generate_consistency_seed(char)
            for char in characters
        ]
        
        combined_seed = "; ".join(character_seeds)
        return f"{combined_seed}, {scene_prompt}"
    
    def validate_character(self, character: Dict[str, Any]) -> bool:
        """Validate character data structure"""
        required_fields = ["name", "gender"]
        return all(field in character for field in required_fields)

