"""
Script Generator Service - AI-powered script generation
"""

import json
import logging
from typing import Dict, List, Any, Optional
from app.config import settings, config_manager
from app.utils.prompts import (
    build_story_expansion_prompt,
    build_script_generation_prompt,
    optimize_prompt_for_veo_ultra
)

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates video scripts using LLM APIs"""
    
    def __init__(self):
        self.provider = config_manager.get("ai.provider", "openai")
        self.model = config_manager.get("ai.model", "gpt-4-turbo-preview")
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
    
    async def generate_script(self, user_prompt: str) -> Dict[str, Any]:
        """
        Generate script from user prompt
        
        Returns:
            {
                "text": script text,
                "scenes": list of scenes,
                "characters": list of characters,
                "metadata": expansion metadata
            }
        """
        try:
            # Step 1: Story expansion
            logger.info("Expanding story...")
            expansion = await self._expand_story(user_prompt)
            
            # Step 2: Generate script
            logger.info("Generating script...")
            script_text = await self._generate_script_text(expansion)
            
            # Step 3: Parse scenes
            logger.info("Parsing scenes...")
            scenes = self._parse_scenes(script_text, expansion)
            
            return {
                "text": script_text,
                "scenes": scenes,
                "characters": expansion.get("characters", []),
                "metadata": expansion
            }
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            raise
    
    async def _expand_story(self, user_prompt: str) -> Dict[str, Any]:
        """Expand user prompt into story breakdown"""
        prompt = build_story_expansion_prompt(user_prompt)
        response = await self._call_llm(prompt)
        
        # Parse JSON response
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
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse expansion JSON: {e}")
            # Return default structure
            return {
                "summary": user_prompt,
                "characters": [],
                "scenes": [{"number": 1, "description": user_prompt, "duration": "10s"}],
                "cinematicStyle": {"camera": "medium", "mood": "neutral", "pacing": "normal"}
            }
    
    async def _generate_script_text(self, expansion: Dict[str, Any]) -> str:
        """Generate script text from expansion"""
        prompt = build_script_generation_prompt(expansion)
        return await self._call_llm(prompt)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API based on provider"""
        if not self.api_key:
            raise ValueError(f"No API key configured for provider: {self.provider}")
        
        if self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.provider == "gemini":
            return await self._call_gemini(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
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
            
            model = genai.GenerativeModel(self.model if "gemini" in self.model else "gemini-pro")
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens
                }
            )
            
            return response.text
        except ImportError:
            raise ImportError("google-generativeai package not installed")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _parse_scenes(self, script_text: str, expansion: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse script text into individual scenes"""
        import re
        
        scenes = []
        scene_regex = r"\[SCENE\s+(\d+)\]([\s\S]*?)(?=\[SCENE|$)"
        matches = re.finditer(scene_regex, script_text, re.IGNORECASE)
        
        expansion_scenes = expansion.get("scenes", [])
        cinematic_style = expansion.get("cinematicStyle", {})
        
        for idx, match in enumerate(matches):
            scene_number = int(match.group(1))
            scene_text = match.group(2).strip()
            
            # Get scene info from expansion
            scene_info = expansion_scenes[idx] if idx < len(expansion_scenes) else {}
            
            # Generate optimized prompt
            scene_description = scene_info.get("description", scene_text[:200])
            prompt = optimize_prompt_for_veo_ultra(
                scene_description,
                cinematic_style,
                expansion.get("characters", [])
            )
            
            scenes.append({
                "number": scene_number,
                "script": scene_text,
                "description": scene_info.get("description", ""),
                "prompt": prompt,
                "duration": scene_info.get("duration", "10s")
            })
        
        # If no scene markers found, create single scene
        if not scenes:
            scenes.append({
                "number": 1,
                "script": script_text,
                "description": expansion.get("summary", ""),
                "prompt": optimize_prompt_for_veo_ultra(
                    expansion.get("summary", script_text[:200]),
                    cinematic_style,
                    expansion.get("characters", [])
                ),
                "duration": "10s"
            })
        
        return scenes

