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
    optimize_prompt_for_veo_ultra,
    build_script_generation_prompt_from_parameters
)

logger = logging.getLogger(__name__)


def _extract_json_block(text: str) -> str:
    """
    Extract the first valid JSON object from text.
    This is tolerant of extra text or truncated output by scanning for the
    longest prefix that parses as JSON.
    """
    # Quick path: if already valid JSON
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Find first '{' and then scan backwards from the end to find a prefix
    # that is valid JSON. This lets us ignore any trailing garbage or
    # partially generated content (e.g., truncated last scene).
    start = text.find("{")
    if start != -1:
        candidate = text[start:]
        for i in range(len(candidate), 0, -1):
            ch = candidate[i - 1]
            if ch not in ("}", "]", "\"", "'"):
                continue
            try:
                prefix = candidate[:i]
                json.loads(prefix)
                return prefix
            except Exception:
                continue

    # Fallback: try to strip markdown fences
    if "```json" in text:
        json_start = text.find("```json") + 7
        json_end = text.find("```", json_start)
        if json_end != -1:
            candidate = text[json_start:json_end].strip()
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                pass

    if "```" in text:
        json_start = text.find("```") + 3
        json_end = text.find("```", json_start)
        if json_end != -1:
            candidate = text[json_start:json_end].strip()
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                pass

    # Last resort: return original text (will error upstream)
    return text


class ScriptGenerator:
    """Generates video scripts using LLM APIs"""
    
    def __init__(self):
        self.provider = config_manager.get("ai.provider", "gemini")
        self.model = config_manager.get("ai.model", "gemini-2.5-flash")
        self.temperature = config_manager.get("ai.temperature", 0.7)
        self.max_tokens = config_manager.get("ai.maxTokens", 2000)
        self.api_key = self._get_api_key()
        
        # Helpful debug log so we always know which LLM/provider is active.
        logger.info(
            "ScriptGenerator initialized with provider=%s, model=%s, api_key_set=%s",
            self.provider,
            self.model,
            bool(self.api_key),
        )
    
    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        if self.provider == "openai":
            return settings.OPENAI_API_KEY
        elif self.provider == "anthropic":
            return settings.ANTHROPIC_API_KEY
        elif self.provider == "gemini":
            return settings.GEMINI_API_KEY
        return ""
    
    async def generate_script_from_parameters(
        self,
        main_content: str,
        video_duration: int,
        style: str,
        target_audience: str,
        aspect_ratio: str,
        language: Optional[str] = None,
        voice_style: Optional[str] = None,
        music_style: Optional[str] = None,
        color_palette: Optional[str] = None,
        transition_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate script from user-specified parameters
        
        Args:
            main_content: Main story/content description
            video_duration: Total video duration in seconds
            style: Visual style (e.g., "cartoon", "3D animation")
            target_audience: Target audience (e.g., "children", "adults")
            aspect_ratio: Video aspect ratio (e.g., "16:9", "9:16")
            language: Optional language/locale
            voice_style: Optional voice style
            music_style: Optional music style
            color_palette: Optional color palette
            transition_style: Optional transition style
            
        Returns:
            Dictionary with script, scenes, characters, and metadata
        """
        try:
            logger.info(
                "generate_script_from_parameters called with provider=%s, model=%s, duration=%s, style=%s, target_audience=%s, aspect_ratio=%s",
                self.provider,
                self.model,
                video_duration,
                style,
                target_audience,
                aspect_ratio,
            )
            
            # Build a rich user prompt that includes all parameters but still goes
            # through the existing, robust generate_script pipeline (story expansion
            # + script text + scene parsing).
            constraint_lines = [
                f"- Total video duration: {video_duration} seconds (target ~8 seconds per scene for Veo 3)",
                f"- Visual style: {style}",
                f"- Target audience: {target_audience}",
                f"- Aspect ratio: {aspect_ratio}",
            ]
            if language:
                constraint_lines.append(f"- Language/Locale: {language}")
            if voice_style:
                constraint_lines.append(f"- Voice style: {voice_style}")
            if music_style:
                constraint_lines.append(f"- Music style: {music_style}")
            if color_palette:
                constraint_lines.append(f"- Color palette: {color_palette}")
            if transition_style:
                constraint_lines.append(f"- Scene transition style: {transition_style}")

            user_prompt = (
                f"{main_content}\n\n"
                "Please create a video script that follows these constraints:\n"
                + "\n".join(constraint_lines)
            )

            # Reuse the existing, battle-tested pipeline
            base_result = await self.generate_script(user_prompt)
            scenes_raw = base_result.get("scenes", [])
            expansion = base_result.get("metadata", {})

            # Derive story structure from expansion if available
            story_structure = expansion.get("storyStructure") or {
                "beginning": main_content,
                "middle": "",
                "end": "",
            }

            # Normalize scenes into the new schema (scene_number + duration_sec)
            import re

            normalized_scenes: List[Dict[str, Any]] = []
            for scene in scenes_raw:
                number = scene.get("scene_number") or scene.get("number", 1)
                description = scene.get("description") or scene.get("script", "")[:200]
                script_text = scene.get("script", "")
                duration_str = str(scene.get("duration", "8s"))
                m = re.search(r"(\\d+)", duration_str)
                duration_sec = int(m.group(1)) if m else 8

                normalized_scenes.append(
                    {
                        "scene_number": int(number),
                        "description": description,
                        "script": script_text,
                        "duration_sec": duration_sec,
                        "visual_style": style,
                        "environment": scene.get("environment", ""),
                        "camera_angle": scene.get("camera_framing", ""),
                        "characters": scene.get("characters", []),
                    }
                )

            script_data: Dict[str, Any] = {
                "story_structure": story_structure,
                "scenes": normalized_scenes,
                "characters": expansion.get("characters", []),
            }

            # Enforce exact total duration with ~8s per scene
            script_data = self._adjust_scene_durations(script_data, video_duration)

            # Regenerate full script text from the normalized data so durations match
            script_text = self._generate_script_text_from_data(script_data)

            result = {
                "text": script_text,
                "scenes": script_data.get("scenes", []),
                "characters": script_data.get("characters", []),
                "story_structure": script_data.get("story_structure", {}),
                "scene_count": len(script_data.get("scenes", [])),
                "total_duration": video_duration,
                "metadata": {
                    "style": style,
                    "target_audience": target_audience,
                    "aspect_ratio": aspect_ratio,
                    "language": language,
                    "voice_style": voice_style,
                    "music_style": music_style,
                    "color_palette": color_palette,
                    "transition_style": transition_style,
                },
            }
            
            # Log a concise preview of the generated script for debugging.
            preview = script_text[:500].replace("\n", " ")
            logger.info(
                "Script generation completed: provider=%s, model=%s, scenes=%d, total_duration=%s, text_preview=%r",
                self.provider,
                self.model,
                result["scene_count"],
                video_duration,
                preview,
            )
            
            return result

        except Exception as e:
            logger.error(f"Failed to generate script from parameters: {e}")
            raise
    
    def _parse_script_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into script data structure"""
        # Always use strict JSON parsing; if it fails, raise and let callers handle it.
        cleaned = _extract_json_block(response)
        try:
            script_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse script JSON. Raw response: %s", response)
            logger.error("Cleaned JSON candidate: %s", cleaned)
            raise ValueError(f"Invalid JSON response from AI: {e}")

        # Ensure required fields are present
        if "scenes" not in script_data:
            script_data["scenes"] = []
        if "characters" not in script_data:
            script_data["characters"] = []
        if "story_structure" not in script_data:
            script_data["story_structure"] = {
                "beginning": "",
                "middle": "",
                "end": ""
            }

        return script_data
    
    def _adjust_scene_durations(self, script_data: Dict[str, Any], target_duration: int) -> Dict[str, Any]:
        """
        Adjust scene durations to sum to target_duration and bias towards ~8s per scene.
        
        - If the LLM produced many very short scenes, we first merge them down to a
          reasonable count based on an ~8s target (so Veo 3's ~8s clips align well).
        - Then we evenly redistribute durations across the merged scenes so that the
          total matches target_duration exactly.
        """
        scenes = script_data.get("scenes", [])
        if not scenes:
            return script_data

        if target_duration <= 0:
            return script_data

        # Desired number of scenes for ~8s each (but at least 1).
        desired_count = max(1, round(target_duration / 8))
        
        logger.info(
            f"Scene duration adjustment: {len(scenes)} scenes provided, "
            f"target_duration={target_duration}s, desired_count={desired_count} (~8s per scene)"
        )

        # If we have more scenes than desired, merge consecutive scenes together so
        # that the count is closer to what Veo 3 will actually render.
        if len(scenes) > desired_count:
            logger.info(
                f"Merging {len(scenes)} scenes down to {desired_count} scenes "
                f"to match Veo 3's ~8s clip generation"
            )
            import math

            group_size = math.ceil(len(scenes) / desired_count)
            merged_scenes: List[Dict[str, Any]] = []

            for idx in range(0, len(scenes), group_size):
                group = scenes[idx : idx + group_size]
                if not group:
                    continue

                first = group[0]
                merged_description = "\n\n".join(
                    [s.get("description", "") for s in group if s.get("description")]
                ).strip()
                merged_script = "\n\n".join(
                    [s.get("script", "") for s in group if s.get("script")]
                ).strip()

                merged_scene = {
                    "scene_number": len(merged_scenes) + 1,
                    "description": merged_description or first.get("description", ""),
                    "script": merged_script or first.get("script", ""),
                    "visual_style": first.get("visual_style"),
                    "environment": first.get("environment"),
                    "camera_angle": first.get("camera_angle") or first.get("camera_framing"),
                    "characters": first.get("characters", []),
                }
                merged_scenes.append(merged_scene)

            scenes = merged_scenes
            script_data["scenes"] = scenes

        scene_count = len(scenes)
        if scene_count == 0:
            return script_data

        # Evenly distribute total seconds across scenes.
        base_duration = target_duration // scene_count
        remainder = target_duration % scene_count

        for i, scene in enumerate(scenes):
            # First `remainder` scenes get +1s so the total matches exactly.
            scene["duration_sec"] = base_duration + (1 if i < remainder else 0)
        
        logger.info(
            f"Final scene distribution: {len(scenes)} scenes, "
            f"durations={[s['duration_sec'] for s in scenes]}, "
            f"total={sum(s['duration_sec'] for s in scenes)}s (target={target_duration}s)"
        )

        return script_data
    
    # Note: No fallback parser here by design. If the AI returns invalid JSON,
    # _parse_script_response will raise a ValueError and the API will surface
    # a clear error to the caller so the prompt or model can be corrected.
    
    def _generate_script_text_from_data(self, script_data: Dict[str, Any]) -> str:
        """Generate script text from structured script data"""
        lines = []
        
        # Add story structure
        story_structure = script_data.get("story_structure", {})
        if story_structure:
            lines.append("STORY STRUCTURE")
            lines.append("=" * 50)
            if story_structure.get("beginning"):
                lines.append(f"\nBEGINNING:\n{story_structure['beginning']}")
            if story_structure.get("middle"):
                lines.append(f"\nMIDDLE:\n{story_structure['middle']}")
            if story_structure.get("end"):
                lines.append(f"\nEND:\n{story_structure['end']}")
            lines.append("\n" + "=" * 50 + "\n")
        
        # Add scenes
        for scene in script_data.get("scenes", []):
            scene_num = scene.get("scene_number", 1)
            description = scene.get("description", "")
            duration = scene.get("duration_sec", 30)
            
            lines.append(f"[SCENE {scene_num}]")
            lines.append(f"Duration: {duration}s")
            lines.append(f"Description: {description}")
            lines.append("")

            # For user-facing text, always prefer the natural-language description.
            # This avoids leaking any internal JSON or debug structures that may be
            # present in the raw `script` field from upstream expansion.
            lines.append(description or scene.get("script", ""))
            lines.append("")

            lines.append("")

        return "\n".join(lines)
    
    async def _call_llm_json(self, prompt: str) -> str:
        """Call LLM API with JSON response format"""
        if not self.api_key:
            raise ValueError(f"No API key configured for provider: {self.provider}")
        
        if self.provider == "openai":
            return await self._call_openai_json(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)  # Anthropic doesn't have JSON mode
        elif self.provider == "gemini":
            # Gemini: request JSON via prompt; response parsing is tolerant
            json_prompt = prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown, no code fences."
            return await self._call_gemini(json_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai_json(self, prompt: str) -> str:
        """Call OpenAI API with JSON response format"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
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
            # fall back to OpenAI so script generation can continue.
            message = str(e).lower()
            if (
                self.provider == "gemini"
                and ("quota" in message or "rate limit" in message or "429" in message)
                and settings.OPENAI_API_KEY
            ):
                logger.warning(
                    "Gemini quota/rate limit hit for script generation; falling back to OpenAI."
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
            # Request JSON directly from Gemini; library 0.8.5+ supports response_mime_type
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
            # Surface quota / rate-limit issues explicitly so callers or tests can skip gracefully.
            if "quota" in message or "rate limit" in message or "429" in message:
                raise RuntimeError(f"Gemini quota or rate limit exceeded: {e}")
            # Provide more helpful error message for genuine model lookup errors.
            if "404" in message or "not found" in message:
                raise ValueError(
                    f"Gemini model '{model_name}' not found. "
                    f"Available models: gemini-1.5-flash, gemini-1.5-pro. "
                    f"Please check your model name in settings."
                )
            # Re-raise anything else for higher-level handling.
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

