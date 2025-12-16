"""
Character Generator Service - AI-powered character DNA generation
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from app.config import settings, config_manager
from app.utils.prompts import build_character_dna_prompt

logger = logging.getLogger(__name__)


class CharacterGenerator:
    """Generates detailed character DNA using LLM APIs"""
    
    def __init__(self):
        self.provider = config_manager.get("ai.provider", "gemini")
        self.model = config_manager.get("ai.model", "gemini-2.5-flash")
        self.temperature = config_manager.get("ai.temperature", 0.7)
        self.max_tokens = config_manager.get("ai.maxTokens", 3000)
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
    
    def extract_characters_from_script(self, script_text: str, script_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Extract character mentions from script
        
        Args:
            script_text: Full script text
            script_data: Optional structured script data with characters list
            
        Returns:
            List of character dictionaries with name and description
        """
        characters = []
        
        # First, try to get characters from structured script data
        if script_data and "characters" in script_data:
            characters = script_data["characters"]
            logger.info(f"Found {len(characters)} characters in structured script data")
            return characters
        
        # Otherwise, try to extract from script text
        # Look for character names (capitalized words that appear multiple times)
        # This is a simple heuristic - can be improved
        words = re.findall(r'\b[A-Z][a-z]+\b', script_text)
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Characters are likely words that appear multiple times and are capitalized
        potential_characters = [word for word, count in word_counts.items() if count >= 2]
        
        for char_name in potential_characters[:10]:  # Limit to top 10
            characters.append({
                "name": char_name,
                "description": f"Character named {char_name}",
                "role": "supporting"
            })
        
        logger.info(f"Extracted {len(characters)} characters from script text")
        return characters
    
    async def generate_character_dna(
        self,
        character_name: str,
        character_description: str,
        script_context: str,
        style: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """
        Generate detailed character DNA using AI
        
        Args:
            character_name: Name of the character
            character_description: Brief description of the character
            script_context: Context from the script/story
            style: Visual style (e.g., "cartoon", "3D animation")
            target_audience: Target audience (e.g., "children", "adults")
            
        Returns:
            Complete character DNA dictionary following template structure
        """
        try:
            prompt = build_character_dna_prompt(
                character_name,
                character_description,
                script_context,
                style,
                target_audience
            )
            
            response = await self._call_llm(prompt)
            
            # Parse JSON response
            character_dna = self._parse_character_dna_response(response)
            
            # Validate character DNA
            self.validate_character_dna(character_dna)
            
            # Set name (in case it wasn't in the response)
            character_dna["name"] = character_name
            
            return character_dna
            
        except Exception as e:
            logger.error(f"Failed to generate character DNA for {character_name}: {e}")
            # Return minimal character DNA as fallback
            return self._create_fallback_character_dna(character_name, character_description)
    
    def _parse_character_dna_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into character DNA dictionary"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            character_dna = json.loads(response)
            
            # Ensure all required fields have defaults
            defaults = {
                "species": "",
                "gender": "unknown",
                "age_description": "",
                "voice_personality": "",
                "body_build": "",
                "face_shape": "",
                "hair": "",
                "skin_or_fur_color": "",
                "signature_feature": "",
                "outfit_top": "",
                "outfit_bottom": "",
                "helmet_or_hat": "",
                "shoes_or_footwear": "",
                "props": "",
                "body_metrics": {}
            }
            
            for key, default_value in defaults.items():
                if key not in character_dna:
                    character_dna[key] = default_value
            
            return character_dna
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse character DNA JSON: {e}")
            raise ValueError(f"Invalid JSON response from AI: {e}")
    
    def validate_character_dna(self, character_dna: Dict[str, Any]) -> bool:
        """
        Validate that character DNA has required fields
        
        Args:
            character_dna: Character DNA dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValueError if validation fails
        """
        required_fields = ["name", "species", "gender"]
        
        for field in required_fields:
            if field not in character_dna or not character_dna[field]:
                raise ValueError(f"Character DNA missing required field: {field}")
        
        return True
    
    def _create_fallback_character_dna(self, name: str, description: str) -> Dict[str, Any]:
        """Create minimal character DNA as fallback"""
        return {
            "name": name,
            "species": "Unknown",
            "gender": "unknown",
            "age_description": "",
            "voice_personality": "",
            "body_build": "",
            "face_shape": "",
            "hair": "",
            "skin_or_fur_color": "",
            "signature_feature": description[:100] if description else "",
            "outfit_top": "",
            "outfit_bottom": "",
            "helmet_or_hat": "",
            "shoes_or_footwear": "",
            "props": "",
            "body_metrics": {}
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
            # fall back to OpenAI so character generation can continue.
            message = str(e).lower()
            if (
                self.provider == "gemini"
                and ("quota" in message or "rate limit" in message or "429" in message)
                and settings.OPENAI_API_KEY
            ):
                logger.warning(
                    "Gemini quota/rate limit hit for character DNA; falling back to OpenAI."
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
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Request JSON response
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

