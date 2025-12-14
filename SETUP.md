# VeoFlow Studio - Setup Guide

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or SQLite for development)
- Redis
- FFmpeg
- Chrome/Chromium browser

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd veoflow-studio/backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

5. **Set up environment variables:**
   ```bash
   cp ../.env.example .env
   # Edit .env and add your API keys:
   # - OPENAI_API_KEY (or ANTHROPIC_API_KEY, GEMINI_API_KEY)
   # - DATABASE_URL (defaults to SQLite)
   # - REDIS_URL (defaults to localhost:6379)
   ```

6. **Initialize database:**
   ```bash
   python init_db.py
   ```

7. **Start FastAPI server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Or use the startup script:
   ```bash
   ./run.sh
   ```

### Celery Worker Setup

In a separate terminal:

```bash
cd veoflow-studio/backend
source venv/bin/activate
celery -A app.workers.render_worker worker --loglevel=info
```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd veoflow-studio/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

### Using Docker Compose

1. **Start all services:**
   ```bash
   cd veoflow-studio
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

## First Time Setup - Google Flow Login

1. Start the backend server
2. The browser will open (if headless=false)
3. Manually log in to Google Flow UI
4. Cookies will be saved for future use

## API Usage Example

### 1. Create a Project

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Video", "description": "Test project"}'
```

### 2. Generate Script

```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/generate-script \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A person walking through a city at sunset"}'
```

### 3. Render a Scene

```bash
curl -X POST "http://localhost:8000/api/render/scenes/{scene_id}/render?project_id={project_id}"
```

### 4. Check Render Status

```bash
curl http://localhost:8000/api/render/tasks/{task_id}
```

### 5. Stitch Videos

```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/stitch \
  -H "Content-Type: application/json" \
  -d '{"transition": "fade", "transition_duration": 0.5}'
```

## Configuration

Edit `backend/veoflow.config.json` to customize:
- Browser settings (headless mode, viewport)
- Flow UI selectors (if Google updates their UI)
- Render timeouts and retry settings
- Video processing options

## Troubleshooting

### Browser Issues
- Ensure Chrome/Chromium is installed
- Check `chromedata/` directory permissions
- Try setting `headless: false` in config for debugging

### Database Issues
- SQLite: Check file permissions
- PostgreSQL: Verify connection string in `.env`

### Redis Issues
- Ensure Redis is running: `redis-cli ping`
- Check REDIS_URL in `.env`

### FFmpeg Issues
- Install FFmpeg: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (Mac)
- Verify installation: `ffmpeg -version`

## Next Steps

1. Configure AI API keys in `.env`
2. Test script generation endpoint
3. Create characters for consistency
4. Start rendering scenes
5. Stitch final video

