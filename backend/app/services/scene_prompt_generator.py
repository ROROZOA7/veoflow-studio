"""
Scene Prompt Generator Service - Generate detailed scene prompts with character consistency
"""

import logging
from typing import Dict, List, Any, Optional
from app.config import settings, config_manager
from app.utils.prompts import build_scene_prompt_generation_prompt

logger = logging.getLogger(__name__)


class ScenePromptGenerator:
    """Generates detailed scene prompts with character consistency"""
    
    def __init__(self):
        self.provider = config_manager.get("ai.provider", "gemini")
        self.model = config_manager.get("ai.model", "gemini-2.5-flash")
        self.temperature = config_manager.get("ai.temperature", 0.7)
        self.max_tokens = config_manager.get("ai.maxTokens", 2000)
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        if self.provider == "openai":
            return settings.OPENAI_API_KEY
        elif self.provider == "anthropic":
            return settings.ANTHROPIC_API_KEY
        elif self.provider == "gemini":
            return settings.GEMINI_API_KEY
        return ""
    
    async def generate_scene_prompts(
        self,
        script_scenes: List[Dict[str, Any]],
        character_dna_list: List[Dict[str, Any]],
        style: str,
        aspect_ratio: str,
        target_audience: str
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed prompts for all scenes
        
        Args:
            script_scenes: List of scene dictionaries from script generation
            character_dna_list: List of character DNA dictionaries
            style: Visual style
            aspect_ratio: Video aspect ratio
            target_audience: Target audience
            
        Returns:
            List of scene dictionaries with detailed prompts
        """
        generated_scenes = []
        
        for scene_data in script_scenes:
            try:
                # Get characters in this scene
                scene_characters = self._get_characters_for_scene(
                    scene_data,
                    character_dna_list
                )
                
                # Generate detailed prompt
                detailed_prompt = await self._generate_detailed_prompt(
                    scene_data,
                    scene_characters,
                    style,
                    aspect_ratio,
                    target_audience
                )
                
                # Create scene-specific character adaptations
                character_adaptations = self._create_character_adaptations(
                    scene_characters,
                    scene_data
                )
                
                generated_scene = {
                    "scene_number": scene_data.get("scene_number", 1),
                    "scene_description": scene_data.get("description", ""),
                    "duration_sec": scene_data.get("duration_sec", 30),
                    "visual_style": scene_data.get("visual_style", style),
                    "environment": scene_data.get("environment", ""),
                    "camera_angle": self._adjust_camera_for_aspect_ratio(
                        scene_data.get("camera_framing", "medium shot"),
                        aspect_ratio
                    ),
                    "prompt": detailed_prompt,
                    "character_adaptations": character_adaptations,
                    "script": scene_data.get("script", "")
                }
                
                generated_scenes.append(generated_scene)
                
            except Exception as e:
                logger.error(f"Failed to generate prompt for scene {scene_data.get('scene_number', 'unknown')}: {e}")
                # Create fallback scene
                generated_scenes.append(self._create_fallback_scene(scene_data, style, aspect_ratio))
        
        return generated_scenes
    
    def _get_characters_for_scene(
        self,
        scene_data: Dict[str, Any],
        character_dna_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get character DNA objects for characters in this scene"""
        scene_character_names = scene_data.get("characters", [])
        if isinstance(scene_character_names, str):
            scene_character_names = [scene_character_names]
        
        scene_characters = []
        for char_name in scene_character_names:
            # Find matching character DNA
            for char_dna in character_dna_list:
                if char_dna.get("name", "").lower() == char_name.lower():
                    scene_characters.append(char_dna)
                    break
        
        return scene_characters
    
    async def _generate_detailed_prompt(
        self,
        scene_data: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style: str,
        aspect_ratio: str,
        target_audience: str
    ) -> str:
        """Generate detailed scene prompt using AI"""
        try:
            prompt = build_scene_prompt_generation_prompt(
                scene_description=scene_data.get("description", ""),
                scene_number=scene_data.get("scene_number", 1),
                duration_sec=scene_data.get("duration_sec", 30),
                characters_with_dna=characters,
                environment=scene_data.get("environment", ""),
                style=style,
                target_audience=target_audience,
                aspect_ratio=aspect_ratio
            )
            
            response = await self._call_llm(prompt)
            
            # Clean up response (remove markdown if present)
            if "```" in response:
                # Extract text between code blocks
                lines = response.split("\n")
                response = "\n".join([line for line in lines if not line.strip().startswith("```")])
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate detailed prompt: {e}")
            # Return basic prompt as fallback
            return self._create_basic_prompt(scene_data, characters, style, aspect_ratio)
    
    def _create_basic_prompt(
        self,
        scene_data: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style: str,
        aspect_ratio: str
    ) -> str:
        """Create basic prompt without AI (fallback)"""
        parts = []
        
        # Add character descriptions
        if characters:
            char_descriptions = []
            for char in characters:
                char_desc = f"{char.get('name', 'Character')}"
                if char.get('species'):
                    char_desc += f" ({char.get('species')})"
                if char.get('body_build'):
                    char_desc += f", {char.get('body_build')}"
                char_descriptions.append(char_desc)
            parts.append(", ".join(char_descriptions))
        
        # Add scene description
        if scene_data.get("description"):
            parts.append(scene_data["description"])
        
        # Add environment
        if scene_data.get("environment"):
            parts.append(f"Environment: {scene_data['environment']}")
        
        # Add style
        parts.append(f"Style: {style}")
        
        # Add camera angle
        camera = self._adjust_camera_for_aspect_ratio(
            scene_data.get("camera_framing", "medium shot"),
            aspect_ratio
        )
        parts.append(f"Camera: {camera}")
        
        return ", ".join(parts)
    
    def _create_character_adaptations(
        self,
        characters: List[Dict[str, Any]],
        scene_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Create scene-specific character adaptations"""
        adaptations = {}
        
        for char in characters:
            char_name = char.get("name", "unknown")
            adaptations[char_name] = {
                "position": char.get("position", ""),
                "orientation": char.get("orientation", ""),
                "pose": char.get("pose", ""),
                "expression": char.get("expression", ""),
                "action": scene_data.get("description", "")
            }
        
        return adaptations
    
    def _adjust_camera_for_aspect_ratio(self, camera_framing: str, aspect_ratio: str) -> str:
        """Adjust camera framing based on aspect ratio"""
        # For vertical (9:16), prefer closer shots
        if aspect_ratio == "9:16":
            if "wide" in camera_framing.lower():
                return camera_framing.replace("wide", "medium").replace("Wide", "Medium")
            return camera_framing
        
        # For horizontal (16:9), can use wider shots
        if aspect_ratio == "16:9":
            return camera_framing
        
        # For square (1:1), prefer medium shots
        if aspect_ratio == "1:1":
            if "wide" in camera_framing.lower():
                return camera_framing.replace("wide", "medium").replace("Wide", "Medium")
            return camera_framing
        
        return camera_framing
    
    def apply_character_to_scene(
        self,
        character_dna: Dict[str, Any],
        scene_context: str
    ) -> Dict[str, Any]:
        """
        Apply character DNA to a specific scene context
        
        Args:
            character_dna: Character DNA dictionary
            scene_context: Description of the scene context
            
        Returns:
            Dictionary with updated prompt and character adaptations
        """
        # Build character description from DNA
        char_desc_parts = []
        
        if character_dna.get("name"):
            char_desc_parts.append(character_dna["name"])
        if character_dna.get("species"):
            char_desc_parts.append(f"({character_dna['species']})")
        if character_dna.get("body_build"):
            char_desc_parts.append(f"with {character_dna['body_build']} build")
        if character_dna.get("face_shape"):
            char_desc_parts.append(f"{character_dna['face_shape']} face")
        if character_dna.get("hair"):
            char_desc_parts.append(f"{character_dna['hair']}")
        if character_dna.get("signature_feature"):
            char_desc_parts.append(f"with {character_dna['signature_feature']}")
        
        character_description = ", ".join(char_desc_parts)
        
        updated_prompt = f"{character_description}, {scene_context}"
        
        character_adaptations = {
            "position": character_dna.get("position", ""),
            "orientation": character_dna.get("orientation", ""),
            "pose": character_dna.get("pose", ""),
            "expression": character_dna.get("expression", ""),
            "action_flow": character_dna.get("action_flow", {})
        }
        
        return {
            "updated_prompt": updated_prompt,
            "character_adaptations": character_adaptations
        }
    
    def _create_fallback_scene(
        self,
        scene_data: Dict[str, Any],
        style: str,
        aspect_ratio: str
    ) -> Dict[str, Any]:
        """Create fallback scene if generation fails"""
        return {
            "scene_number": scene_data.get("scene_number", 1),
            "scene_description": scene_data.get("description", ""),
            "duration_sec": scene_data.get("duration_sec", 30),
            "visual_style": style,
            "environment": scene_data.get("environment", ""),
            "camera_angle": "medium shot",
            "prompt": scene_data.get("description", ""),
            "character_adaptations": {},
            "script": scene_data.get("script", "")
        }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API based on provider"""
        if not self.api_key:
            raise ValueError(f"No API key configured for provider: {self.provider}")
        
        try:
            if self.provider == "openai":
                return await self._call_openai(prompt)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt)
            elif self.provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            # If Gemini hits quota/rate limits and we have an OpenAI key, transparently
            # fall back to OpenAI so scene prompt generation can continue.
            message = str(e).lower()
            if (
                self.provider == "gemini"
                and ("quota" in message or "rate limit" in message or "429" in message)
                and settings.OPENAI_API_KEY
            ):
                logger.warning(
                    "Gemini quota/rate limit hit for scene prompts; falling back to OpenAI."
                )
                self.provider = "openai"
                self.model = self.model if "gpt" in self.model else "gpt-4o-mini"
                self.api_key = settings.OPENAI_API_KEY
                return await self._call_openai(prompt)
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model if "claude" in self.model else "claude-3-opus-20240229",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Use the configured model, default to gemini-2.5-flash if not specified
            model_name = self.model if self.model and "gemini" in self.model.lower() else "gemini-2.5-flash"
            
            # Ensure model name doesn't have "models/" prefix (library adds it automatically)
            if model_name.startswith("models/"):
                model_name = model_name.replace("models/", "")
            
            logger.info(f"Using Gemini model: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
            )
            
            return response.text
                
        except ImportError:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            message = str(e).lower()
            # Surface quota / rate-limit issues explicitly.
            if "quota" in message or "rate limit" in message or "429" in message:
                raise RuntimeError(f"Gemini quota or rate limit exceeded: {e}")
            # Provide more helpful error message for genuine model lookup errors.
            if "404" in message or "not found" in message:
                raise ValueError(
                    f"Gemini model '{model_name}' not found. "
                    f"Available models: gemini-1.5-flash, gemini-1.5-pro. "
                    f"Please check your model name in settings."
                )
            raise

