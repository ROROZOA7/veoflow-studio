# Video Script Generation Feature - Requirements & Design

## Overview

This document outlines the requirements and design for a new feature that helps users create complete video scripts from an initial idea, with consistent characters across scenes and detailed scene prompts.

## Current State

### What We Have
- ✅ Video rendering from individual scene prompts
- ✅ Scene management (create, edit, delete scenes)
- ✅ Character DNA model (basic character definitions)
- ✅ Project and scene structure
- ✅ Flow automation for video generation

### What We're Missing
- ❌ Script generation from initial idea/concept
- ❌ Character consistency across multiple scenes
- ❌ Detailed character design following templates
- ❌ Scene-by-scene breakdown with detailed prompts
- ❌ Character appearance consistency tracking
- ❌ Story structure and narrative flow

---

## Feature Goals

### Primary Goals
1. **Generate complete video scripts** from a simple initial idea or concept
2. **Maintain character consistency** across all scenes in a video
3. **Create detailed character designs** following structured templates
4. **Generate scene-by-scene prompts** with detailed descriptions
5. **Ensure visual continuity** between scenes

### User Experience Goals
- User provides parameters:
  - Main content: "The story of the tortoise and the hare"
  - Video duration: "300s"
  - Style: "cartoon"
  - Target audience: "children"
  - Aspect ratio: "16:9"
- System generates:
  - Complete script with multiple scenes (calculated from duration)
  - Detailed character designs (Tortoise, Hare with all attributes)
  - Scene-by-scene breakdown with detailed prompts
  - Character consistency rules for each scene
  - All scenes automatically created in the project
  - User can edit characters and scenes before rendering

---

## Requirements

### 1. Script Generation from User-Specified Parameters

#### User Input Parameters
Users must specify the following parameters to generate a complete script:

1. **Main Content/Story** (Required)
   - Free-form text describing the video concept or story
   - Example: "The story of the tortoise and the hare"
   - Example: "A story about a teacher bunny teaching kids about gardening"

2. **Video Duration** (Required)
   - Total video duration in seconds
   - Example: "300s" (5 minutes)
   - Example: "180s" (3 minutes)
   - Used to calculate number of scenes and scene durations

3. **Style** (Required)
   - Visual/animation style for the video
   - Examples: "cartoon", "3D animation", "realistic", "Pixar style", "anime"
   - Affects character design and scene visual descriptions

4. **Target Audience** (Required)
   - Intended audience for the video
   - Examples: "children", "adults", "teenagers", "educational", "entertainment"
   - Affects story complexity, character design, and content appropriateness

5. **Aspect Ratio** (Required)
   - Video aspect ratio
   - Examples: "16:9", "9:16", "1:1", "4:3"
   - Affects scene composition and camera framing

6. **Other Optional Parameters** (To be discussed)
   - Language/Locale (e.g., "en-US", "vi-VN")
   - Voice style (e.g., "narrator", "character voices")
   - Music style (e.g., "upbeat", "calm", "dramatic")
   - Color palette (e.g., "bright", "muted", "pastel")
   - Scene transition style (e.g., "smooth", "cut", "fade")

#### Output
- **Complete Video Script** with:
  - Story structure (beginning, middle, end)
  - Scene breakdown (number of scenes calculated based on total duration)
  - Scene descriptions with durations
  - Character introductions
  - Narrative flow
  - All scenes created in the project database

#### Requirements
- Use AI service (OpenAI, Anthropic, etc.) to generate script
- Calculate number of scenes based on total duration (e.g., 300s = ~6-10 scenes of 5-10 seconds each)
- Apply user-specified style, target audience, and aspect ratio to script generation
- Support multiple story structures (linear, episodic, etc.)
- Generate appropriate scene durations that sum to total video duration
- Include scene transitions and narrative flow
- Create all scene objects in the project database automatically

---

### 2. Character Design & Consistency

#### Character Template Structure
Based on the example image, characters need detailed attributes:

```json
{
  "id": "CHAR_1",
  "name": "Teacher Bunny",
  "species": "Rabbit - White Rabbit",
  "gender": "Male",
  "age": "Mature",
  "voice_personality": "Gentle, clear; gender=Male; locale=vi-VN; accent=Northern Vietnamese, Rabbit-like",
  "body_build": "Chubby, soft",
  "face_shape": "Round",
  "hair": "White fur",
  "skin_or_fur_color": "Soft white fur",
  "signature_feature": "Round glasses; gentle, warm smile",
  "outfit_top": "Green gardening apron",
  "outfit_bottom": "",
  "helmet_or_hat": "Light brown straw hat",
  "shoes_or_footwear": "Furry paws",
  "props": "Tiny wooden watering can, woven basket",
  "body_metrics": {
    "unit": "cm",
    "height": 45,
    "head": 12,
    "shoulder": 15,
    "torso": 30,
    "tail": 10,
    "paws": 8
  },
  "position": "kneeling beside young tomato plants",
  "orientation": "angled down towards plants",
  "pose": "kneeling",
  "foot_placement": "paws tucked under body",
  "hand_detail": "right paw gently presses soil",
  "expression": "calm expression",
  "action_flow": {
    "pre_action": "approaching young tomato plants",
    "main_action": "kneeling down gently, pressing soil with careful paw movements, checking plant health"
  }
}
```

#### Character Consistency Requirements
- **Visual Consistency**: Same character appearance across all scenes
  - Same body metrics
  - Same outfit (unless story requires change)
  - Same signature features
  - Same color palette

- **Behavioral Consistency**: Character personality and actions remain consistent
  - Same voice personality
  - Consistent expressions
  - Logical action flow

- **Scene-Specific Adaptations**: Allow for context-appropriate changes
  - Different poses/positions per scene
  - Different props per scene (if story requires)
  - Different expressions (but consistent personality)

#### Character Generation Process
1. **Extract Characters** from script/story
2. **Generate Character DNA** using AI with detailed template
   - Apply user-specified style (e.g., "cartoon" style affects character design)
   - Apply target audience (e.g., "children" affects character appearance and personality)
3. **Validate Character Design** (ensure all required fields)
4. **Store Character DNA** in database
5. **Apply Character to Scenes** with scene-specific adaptations
6. **User can edit** character designs before proceeding

---

### 3. Scene Generation with Detailed Prompts

#### Scene Template Structure
Each scene should include:

```json
{
  "scene_id": "2",
  "scene_number": 2,
  "duration_sec": 8,
  "visual_style": "High-quality 3D animation in Pixar's signature style, appealing character design with subtle details",
  "scene_description": "Teacher Bunny demonstrates proper planting technique",
  "characters": [
    {
      "character_id": "CHAR_1",
      "position": "kneeling beside young tomato plants",
      "orientation": "angled down towards plants",
      "pose": "kneeling",
      "expression": "calm expression",
      "action": "demonstrating planting technique",
      "props": ["watering can", "basket"]
    }
  ],
  "environment": "Garden with young tomato plants, soft morning light",
  "camera_angle": "Medium shot, slightly angled down",
  "prompt": "Detailed prompt combining all elements for video generation"
}
```

#### Scene Prompt Generation
- Combine character details with scene context
- Apply user-specified style, target audience, and aspect ratio
- Include visual style, environment, camera angles (adjusted for aspect ratio)
- Ensure character consistency from Character DNA
- Generate detailed, actionable prompts for video generation
- Calculate scene durations to match total video duration

#### Scene Generation Process
1. **Break Down Script** into individual scenes
   - Calculate number of scenes based on total duration
   - Distribute duration across scenes (e.g., 300s = 6 scenes of ~50s each, or 10 scenes of ~30s each)
2. **Assign Characters** to each scene
3. **Generate Scene Context** (environment, camera, lighting)
   - Apply aspect ratio to camera framing
   - Apply style to visual descriptions
   - Apply target audience to content appropriateness
4. **Create Detailed Prompts** combining:
   - Character appearance (from Character DNA)
   - Character position/pose (scene-specific)
   - Environment description
   - Visual style (from user input)
   - Camera angles (adjusted for aspect ratio)
   - Scene duration
5. **Create Scene Objects** in database automatically
6. **Validate Scene Prompts** (ensure completeness)
7. **User can edit** scene prompts before rendering

---

## System Architecture

### High-Level Flow

```
User Input Parameters:
- Main Content/Story
- Video Duration
- Style
- Target Audience
- Aspect Ratio
- (Other parameters)
    ↓
[Script Generator Service]
    ↓
Complete Script (Story + Scene Breakdown)
    - Number of scenes calculated from duration
    - Scene durations distributed
    ↓
[Character Extractor & Generator]
    ↓
Character DNA Objects (Detailed Character Designs)
    - Applied style and target audience
    ↓
[User Review & Edit] (Optional)
    - User can edit characters
    ↓
[Scene Generator Service]
    ↓
Scene Objects with Detailed Prompts
    - All scenes created in database
    - Applied style, aspect ratio, target audience
    ↓
[User Review & Edit] (Optional)
    - User can edit scene prompts
    ↓
[Video Renderer] (Existing)
    ↓
Complete Video
```

### Components Needed

#### 1. Script Generator Service
- **Input**: Initial concept/idea
- **Output**: Complete script with scene breakdown
- **AI Service**: OpenAI GPT-4, Anthropic Claude, etc.
- **Responsibilities**:
  - Generate story structure
  - Break down into scenes
  - Create scene descriptions
  - Identify characters

#### 2. Character Extractor & Generator
- **Input**: Script with character mentions
- **Output**: Character DNA objects
- **AI Service**: Same as Script Generator
- **Responsibilities**:
  - Extract character mentions from script
  - Generate detailed character designs using template
  - Ensure character consistency rules
  - Store Character DNA in database

#### 3. Scene Generator Service
- **Input**: Script scenes + Character DNA
- **Output**: Scene objects with detailed prompts
- **AI Service**: Same as Script Generator
- **Responsibilities**:
  - Generate scene-specific character adaptations
  - Create environment descriptions
  - Combine elements into detailed prompts
  - Ensure visual continuity between scenes

#### 4. Character DNA Manager
- **Responsibilities**:
  - Store and retrieve Character DNA
  - Apply character to scenes
  - Validate character consistency
  - Manage character updates

---

## Database Schema Changes

### Character DNA Model (Enhancement)
Current model exists but needs enhancement:

```python
class CharacterDNA(Base):
    id: str
    project_id: str
    name: str
    species: str
    gender: str
    age: str
    voice_personality: str
    body_build: str
    face_shape: str
    hair: str
    skin_or_fur_color: str
    signature_feature: str
    outfit_top: str
    outfit_bottom: str
    helmet_or_hat: str
    shoes_or_footwear: str
    props: str  # JSON array
    body_metrics: str  # JSON object
    # ... other fields from template
```

### Scene Model (Enhancement)
Current model exists but needs enhancement:

```python
class Scene(Base):
    id: str
    project_id: str
    number: int
    prompt: str  # Current: simple prompt
    # New fields needed:
    scene_description: str
    duration_sec: int
    visual_style: str
    environment: str
    camera_angle: str
    character_adaptations: str  # JSON: scene-specific character details
    # ... other fields from template
```

### Script Model (New)
```python
class Script(Base):
    id: str
    project_id: str
    main_content: str  # User input: main story/content
    video_duration: int  # User input: total duration in seconds
    style: str  # User input: visual style
    target_audience: str  # User input: target audience
    aspect_ratio: str  # User input: aspect ratio
    language: str  # Optional: language/locale
    voice_style: str  # Optional: voice style
    music_style: str  # Optional: music style
    color_palette: str  # Optional: color palette
    transition_style: str  # Optional: transition style
    full_script: str  # Generated: complete script text
    story_structure: str  # JSON: beginning, middle, end
    scene_count: int  # Calculated: number of scenes
    generated_at: datetime
```

---

## API Endpoints Needed

### 1. Generate Script from Parameters
```
POST /api/projects/{project_id}/generate-script
Body: {
  "main_content": "The story of the tortoise and the hare",
  "video_duration": 300,  // in seconds
  "style": "cartoon",
  "target_audience": "children",
  "aspect_ratio": "16:9",
  "language": "en-US",  // optional
  "voice_style": "narrator",  // optional
  "music_style": "upbeat",  // optional
  "color_palette": "bright",  // optional
  "transition_style": "smooth"  // optional
}
Response: {
  "script_id": "...",
  "scenes": [
    {
      "scene_id": "...",
      "scene_number": 1,
      "duration_sec": 50,
      "description": "...",
      "prompt": "..."
    }
  ],
  "characters": [
    {
      "character_id": "...",
      "name": "Tortoise",
      "character_dna": {...}
    }
  ],
  "total_duration": 300,
  "scene_count": 6
}
```

### 2. Generate Character DNA
```
POST /api/projects/{project_id}/characters/generate
Body: {
  "character_name": "Tortoise",
  "character_description": "...",
  "script_context": "...",
  "style": "cartoon",  // from user input
  "target_audience": "children"  // from user input
}
Response: {
  "character_id": "...",
  "character_dna": {...}
}
```

### 2b. Edit Character DNA
```
PUT /api/projects/{project_id}/characters/{character_id}
Body: {
  "name": "Tortoise",
  "species": "Tortoise",
  "gender": "Male",
  // ... all character DNA fields
}
Response: {
  "character_id": "...",
  "character_dna": {...}
}
```

### 3. Generate Scene Prompts
```
POST /api/projects/{project_id}/scenes/generate-prompts
Body: {
  "script_id": "...",
  "character_dna": [...],
  "style": "cartoon",  // from user input
  "aspect_ratio": "16:9",  // from user input
  "target_audience": "children"  // from user input
}
Response: {
  "scenes": [
    {
      "scene_id": "...",
      "scene_number": 1,
      "duration_sec": 50,
      "detailed_prompt": "...",
      "character_adaptations": {...}
    }
  ],
  "total_scenes_created": 6
}
```

### 3b. Edit Scene
```
PUT /api/projects/{project_id}/scenes/{scene_id}
Body: {
  "prompt": "Updated detailed prompt...",
  "duration_sec": 45,
  "description": "Updated scene description",
  "character_adaptations": {...}
}
Response: {
  "scene_id": "...",
  "scene": {...}
}
```

### 4. Apply Character to Scene
```
POST /api/scenes/{scene_id}/apply-character
Body: {
  "character_id": "...",
  "scene_context": "..."
}
Response: {
  "updated_prompt": "...",
  "character_adaptations": {...}
}
```

---

## AI Prompt Engineering

### Script Generation Prompt Template
```
You are a professional video script writer. Generate a complete video script based on the following parameters:

Main Content/Story: {main_content}
Total Video Duration: {video_duration} seconds
Style: {style}
Target Audience: {target_audience}
Aspect Ratio: {aspect_ratio}

Requirements:
1. Create a story with clear beginning, middle, and end
2. Break down into scenes where:
   - Total duration of all scenes = {video_duration} seconds
   - Each scene should be 30-60 seconds long (adjust based on total duration)
   - Number of scenes should be calculated: {video_duration} / 40-50 seconds per scene
3. Identify all characters that appear
4. Create scene descriptions with visual details appropriate for:
   - Style: {style}
   - Target Audience: {target_audience}
   - Aspect Ratio: {aspect_ratio} (affects camera framing)
5. Ensure story is appropriate for {target_audience}

Output format: JSON with structure:
{
  "story_structure": {
    "beginning": "...",
    "middle": "...",
    "end": "..."
  },
  "scenes": [
    {
      "scene_number": 1,
      "description": "...",
      "characters": ["Character Name"],
      "duration_sec": 50,
      "visual_style": "{style}",
      "camera_framing": "adjusted for {aspect_ratio}"
    }
  ],
  "characters": [
    {
      "name": "Character Name",
      "role": "...",
      "description": "..."
    }
  ],
  "total_duration": {video_duration},
  "scene_count": <calculated>
}
```

### Character DNA Generation Prompt Template
```
You are a character designer. Create a detailed character design based on the following information:

Character Name: {character_name}
Character Description: {character_description}
Script Context: {script_context}
Style: {style}
Target Audience: {target_audience}

Generate a complete character design following this template:
Note: The character should be designed in {style} style and be appropriate for {target_audience} audience.
{
  "name": "...",
  "species": "...",
  "gender": "...",
  "age": "...",
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
  "body_metrics": {
    "unit": "cm",
    "height": ...,
    "head": ...,
    "shoulder": ...,
    "torso": ...,
    "tail": ...,
    "paws": ...
  }
}

Ensure the character design is:
- Detailed and specific
- Consistent with the story context
- Suitable for 3D animation
- Visually appealing
```

### Scene Prompt Generation Prompt Template
```
You are a video scene director. Create a detailed scene prompt for video generation.

Scene Description: {scene_description}
Scene Number: {scene_number}
Scene Duration: {duration_sec} seconds
Characters in Scene: {characters_with_dna}
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
Ensure the prompt maintains character consistency and fits the {duration_sec} second duration.
```

---

## User Workflow

### Step 1: Parameter Input
1. User navigates to project
2. Clicks "Generate Script from Parameters" or "Create Script"
3. Fills in required parameters:
   - **Main Content**: "The story of the tortoise and the hare"
   - **Video Duration**: "300" (seconds)
   - **Style**: "cartoon" (dropdown or text input)
   - **Target Audience**: "children" (dropdown)
   - **Aspect Ratio**: "16:9" (dropdown)
   - **Optional parameters** (if needed)
4. Clicks "Generate Script"

### Step 2: Script Generation
1. System generates complete script based on parameters
   - Calculates number of scenes from duration (e.g., 300s = 6-10 scenes)
   - Distributes scene durations
   - Applies style, target audience, aspect ratio
2. Shows script preview with scene breakdown
   - Total duration: 300s
   - Number of scenes: 6
   - Scene durations: [50s, 50s, 50s, 50s, 50s, 50s]
3. User can review and edit script
4. User clicks "Continue to Characters"

### Step 3: Character Design
1. System extracts characters from script
2. For each character, generates detailed Character DNA
   - Applies user-specified style (e.g., "cartoon" style)
   - Applies target audience (e.g., "children" - friendly, colorful)
3. Shows character design preview for each character
4. **User can review and edit character designs** (important feature)
   - Edit any character DNA field
   - Add/remove characters
   - Modify character attributes
5. User clicks "Continue to Scenes"

### Step 4: Scene Prompt Generation
1. System generates detailed prompts for each scene
   - Applies character consistency to each scene
   - Applies style, aspect ratio, target audience
   - Calculates and assigns scene durations
2. **All scenes are automatically created in the project database**
3. Shows scene prompts preview
   - List of all scenes with durations
   - Preview of each scene prompt
4. **User can review and edit scene prompts** (important feature)
   - Edit scene prompts
   - Adjust scene durations (must sum to total duration)
   - Modify scene descriptions
   - Reorder scenes
5. User clicks "Generate Videos" or "Start Rendering"

### Step 5: Video Rendering (Existing)
1. System renders each scene using detailed prompts
2. User can monitor progress
3. Videos are generated and stitched together

---

## Technical Considerations

### 1. AI Service Integration
- **Current**: Script generation uses OpenAI (if configured)
- **Need**: Enhance to support script, character, and scene generation
- **Consideration**: Token costs for multiple AI calls
- **Solution**: Batch requests where possible, cache results

### 2. Character Consistency Enforcement
- **Challenge**: Ensuring character appearance remains consistent across scenes
- **Solution**: 
  - Store Character DNA as source of truth
  - Apply character DNA to each scene prompt
  - Validate prompts include character details
  - Use AI to ensure consistency in generated prompts

### 3. Template Validation
- **Challenge**: Ensuring generated content follows template structure
- **Solution**:
  - Use structured output (JSON mode) from AI
  - Validate against schema
  - Retry generation if validation fails
  - Provide fallback templates

### 4. Performance
- **Challenge**: Multiple AI calls can be slow
- **Solution**:
  - Use async processing
  - Show progress to user
  - Cache intermediate results
  - Allow user to proceed with partial results

### 5. Error Handling
- **Challenge**: AI generation can fail or produce invalid output
- **Solution**:
  - Retry with different prompts
  - Provide manual editing interface
  - Validate all generated content
  - Log errors for debugging

---

## Open Questions & Decisions Needed

### 1. User Input Parameters
- **Question**: Are all listed parameters required, or should some be optional?
- **Required Parameters**: main_content, video_duration, style, target_audience, aspect_ratio
- **Optional Parameters**: language, voice_style, music_style, color_palette, transition_style
- **Recommendation**: Make required parameters mandatory, optional parameters have sensible defaults

### 2. AI Service Choice
- **Question**: Which AI service to use? (OpenAI, Anthropic, local model?)
- **Considerations**: Cost, quality, availability, API limits
- **Recommendation**: Support multiple providers, allow configuration

### 3. Character DNA Completeness
- **Question**: Should all template fields be required or optional?
- **Consideration**: Some fields may not apply to all characters
- **Recommendation**: Required fields: name, species, basic appearance. Optional: detailed metrics, props

### 4. Scene Prompt Length
- **Question**: How detailed should scene prompts be?
- **Consideration**: Longer prompts = better quality but higher token costs
- **Recommendation**: Detailed but concise, focus on essential visual elements

### 5. Character Consistency Strictness
- **Question**: How strictly should character consistency be enforced?
- **Consideration**: Some story changes may require character updates
- **Recommendation**: Allow scene-specific adaptations but maintain core appearance

### 6. User Editing Capability
- **Question**: How much can users edit generated content?
- **Consideration**: Balance between automation and user control
- **Requirement**: **Users MUST be able to edit characters and scenes** (as specified)
- **Recommendation**: 
  - Allow editing at all stages (script, character, scene prompts)
  - Provide easy-to-use editing interface
  - Save edits immediately
  - Allow re-generation if user wants to start over

### 7. Multi-Character Scenes
- **Question**: How to handle scenes with multiple characters?
- **Consideration**: Each character needs individual attention
- **Recommendation**: Generate prompts that include all characters with their individual details

### 8. Scene Duration Calculation
- **Question**: How to calculate and distribute scene durations?
- **Consideration**: Total duration must match user input exactly
- **Recommendation**: 
  - Calculate number of scenes: total_duration / average_scene_duration (40-50s)
  - Distribute duration evenly or based on story importance
  - Allow user to adjust individual scene durations (with validation that sum = total)

### 9. Story Structure Templates
- **Question**: Should we provide story structure templates?
- **Consideration**: Different video types need different structures
- **Recommendation**: Support multiple templates (linear, episodic, educational, etc.)

---

## Implementation Phases

### Phase 1: Script Generation (MVP)
- Generate script from initial concept
- Basic scene breakdown
- Store script in database
- **Timeline**: 1-2 weeks

### Phase 2: Character DNA Generation
- Extract characters from script
- Generate Character DNA using template
- Store Character DNA
- **Timeline**: 1-2 weeks

### Phase 3: Scene Prompt Generation
- Generate detailed scene prompts
- Apply character consistency
- Combine all elements
- **Timeline**: 1-2 weeks

### Phase 4: Integration & Polish
- Integrate with existing render system
- Add user editing capabilities
- Error handling and validation
- **Timeline**: 1 week

### Phase 5: Advanced Features
- Multi-character scenes
- Story structure templates
- Character consistency validation
- **Timeline**: 2-3 weeks

---

## Success Metrics

### Functional Metrics
- ✅ Scripts generated successfully from concepts
- ✅ Characters maintain consistency across scenes
- ✅ Scene prompts are detailed and actionable
- ✅ Videos generated match script intent

### User Experience Metrics
- ✅ Users can generate complete scripts in < 5 minutes
- ✅ Generated content quality is acceptable (user satisfaction)
- ✅ Users can easily edit generated content
- ✅ Error rate < 5%

### Technical Metrics
- ✅ AI generation success rate > 95%
- ✅ Average generation time < 2 minutes
- ✅ API response time < 30 seconds per step

---

## Next Steps

1. **Review this document** with stakeholders
2. **Decide on AI service** and configuration
3. **Finalize template structures** (Character DNA, Scene)
4. **Create detailed API specifications**
5. **Design database schema changes**
6. **Plan implementation phases**
7. **Create user interface mockups**
8. **Begin Phase 1 implementation**

---

## References

- Current Character DNA model: `app/models/character.py`
- Current Scene model: `app/models/scene.py`
- Example character template: See attached image
- Current script generation: `app/services/script_generator.py` (if exists)

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-14  
**Status**: Draft - Awaiting Review

