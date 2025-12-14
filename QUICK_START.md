# VeoFlow Studio - Quick Start Guide

## Complete Video Generation Flow

This guide walks you through generating your first video using VeoFlow Studio.

### Step 1: Setup Backend

```bash
cd veoflow-studio/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp ../.env.example .env
# Edit .env and add your OPENAI_API_KEY (or ANTHROPIC_API_KEY/GEMINI_API_KEY)

# Initialize database
python init_db.py
```

### Step 2: Start Services

**Terminal 1 - FastAPI Server:**
```bash
cd veoflow-studio/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Celery Worker:**
```bash
cd veoflow-studio/backend
source venv/bin/activate
celery -A app.workers.render_worker worker --loglevel=info
```

**Terminal 3 - Redis (if not running):**
```bash
redis-server
```

### Step 3: Test the Flow

Run the test script to verify everything works:

```bash
cd veoflow-studio/backend
source venv/bin/activate
python test_flow.py
```

### Step 4: Generate Your First Video

#### Using cURL:

1. **Create Project:**
```bash
PROJECT_RESPONSE=$(curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Video", "description": "Test"}')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.id')
echo "Project ID: $PROJECT_ID"
```

2. **Generate Script:**
```bash
curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/generate-script \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A person walking through a beautiful city at sunset, cinematic style"}'
```

3. **Get Scenes:**
```bash
SCENES=$(curl http://localhost:8000/api/scenes?project_id=$PROJECT_ID)
SCENE_ID=$(echo $SCENES | jq -r '.[0].id')
echo "Scene ID: $SCENE_ID"
```

4. **Start Rendering:**
```bash
RENDER_RESPONSE=$(curl -X POST "http://localhost:8000/api/render/scenes/$SCENE_ID/render?project_id=$PROJECT_ID")
TASK_ID=$(echo $RENDER_RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"
```

5. **Check Status:**
```bash
curl http://localhost:8000/api/render/tasks/$TASK_ID
```

6. **After all scenes are rendered, stitch them:**
```bash
curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/stitch \
  -H "Content-Type: application/json" \
  -d '{"transition": "fade", "transition_duration": 0.5}'
```

### Step 5: Access Generated Videos

Videos are saved in:
- Individual scenes: `veoflow-studio/output/{project_id}/scene_{scene_id}.mp4`
- Final stitched video: `veoflow-studio/output/{project_id}/final_{project_id}.mp4`

## Important Notes

1. **First Time Login**: When you first run a render, the browser will open. You need to manually log in to Google Flow UI. After that, cookies are saved.

2. **Render Time**: Each scene takes 2-4 minutes to render. Be patient!

3. **API Keys**: Make sure you have configured at least one AI API key in `.env`:
   - `OPENAI_API_KEY` for OpenAI GPT models
   - `ANTHROPIC_API_KEY` for Claude models
   - `GEMINI_API_KEY` for Google Gemini models

4. **Browser**: Keep browser visible (headless=false) for first login. You can set `headless: true` in `veoflow.config.json` after logging in.

## Troubleshooting

- **"Could not find prompt input"**: Google Flow UI may have changed. Update selectors in `veoflow.config.json`
- **"Render timeout"**: Increase `timeoutGenerateMs` in config
- **"No API key"**: Check your `.env` file has the correct API key set
- **Database errors**: Run `python init_db.py` to recreate tables

## Next Steps

- Create characters for consistency across scenes
- Use the frontend UI (when implemented) for easier workflow
- Customize prompts in the scene editor
- Experiment with different transitions

