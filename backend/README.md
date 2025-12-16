# VeoFlow Studio Backend

FastAPI backend for VeoFlow Studio video generation application.

## Introduction

VeoFlow Studio Backend is a powerful Python-based API server that automates the creation of videos using Google Veo 3 Ultra through browser automation. The backend orchestrates the entire video generation workflow, from script creation to final video stitching.

### What It Does

The backend provides a complete automation solution for video generation:

1. **Script Generation**: Uses AI (OpenAI, Anthropic, or Gemini) to generate video scripts from text prompts
2. **Scene Breakdown**: Automatically breaks scripts into scenes with optimized prompts for Veo Ultra
3. **Character Management**: Maintains character consistency across scenes using DNA-based system
4. **Browser Automation**: Uses Playwright to interact with Google Flow UI for video rendering
5. **Video Processing**: Stitches rendered scenes together with transitions using FFmpeg
6. **Job Queue**: Manages async rendering tasks using Celery and Redis

### Key Technologies

- **FastAPI**: Modern, fast web framework for building APIs
- **Playwright**: Browser automation for Google Flow UI interaction
- **Celery**: Distributed task queue for async video rendering
- **SQLAlchemy**: Database ORM for data persistence
- **FFmpeg**: Video processing and stitching

## Building and Installation

### Prerequisites

Before building the project, ensure you have the following installed:

- **Python 3.10+** - Required Python version
- **PostgreSQL** (or SQLite for development) - Database
- **Redis** - Required for Celery task queue
- **FFmpeg** - Video processing
- **Chrome/Chromium** - Browser for automation
- **Git** - Version control

### Installation Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd veoflow-studio/backend
```

#### 2. Create Virtual Environment

Using Python's built-in venv:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Or using `uv` (recommended):

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies

Using pip:

```bash
pip install -r requirements.txt
```

Or using `uv`:

```bash
uv pip install -r requirements.txt
```

#### 4. Install Playwright Browsers

Playwright requires browser binaries to be installed separately:

```bash
playwright install chromium
```

#### 5. Set Up Environment Variables

Create a `.env` file in the backend directory:

```bash
cp ../.env.example .env
```

Edit `.env` and configure the following:

```env
# AI API Keys (at least one required)
OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GEMINI_API_KEY=your_gemini_key_here

# Database
DATABASE_URL=sqlite:///./veoflow.db  # For SQLite (development)
# DATABASE_URL=postgresql://user:password@localhost/veoflow  # For PostgreSQL

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Flow
FLOW_URL=https://flow.google.com/your-project-url

# Browser Settings
BROWSER_HEADLESS=false  # Set to true for headless mode

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000
```

#### 6. Initialize Database

Run the database initialization script:

```bash
python init_db.py
```

Or if using Alembic migrations:

```bash
alembic upgrade head
```

#### 7. Start Redis (Required for Celery)

On Linux/Mac:

```bash
redis-server
```

Or using Docker:

```bash
docker run -d -p 6379:6379 redis:latest
```

#### 8. Verify Installation

Check that all dependencies are installed correctly:

```bash
python -c "import fastapi, playwright, celery, redis, sqlalchemy; print('All dependencies installed!')"
```

### Running the Application

#### Option 1: Using the Startup Script

The easiest way to start the backend:

```bash
chmod +x run.sh
./run.sh
```

This script will:
- Create virtual environment if it doesn't exist
- Install dependencies
- Install Playwright browsers
- Initialize database
- Start the FastAPI server

#### Option 2: Manual Start

Start the FastAPI server:

```bash
source venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "profiles/*" --reload-exclude "output/*" --reload-exclude "logs/*" --reload-exclude "images/*" --reload-exclude "venv/*" --reload-exclude "chromedata/*" --reload-exclude "**/__pycache__/*"
```

#### Option 3: Using Docker

If using Docker Compose (from project root):

```bash
cd ../..
docker-compose up -d backend
```

### Starting Celery Worker

The Celery worker handles async video rendering tasks. Start it in a separate terminal:

```bash
cd veoflow-studio/backend
source venv/bin/activate
celery -A app.workers.render_worker worker --loglevel=info
```

### Verify Installation

1. **Check API Health**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status": "healthy"}`

2. **Check API Root**:
   ```bash
   curl http://localhost:8000/
   ```
   Should return API information

3. **Check Setup Status**:
   ```bash
   curl http://localhost:8000/api/setup/status
   ```
   Should return setup status information

### First-Time Setup - Google Flow Login

After starting the backend:

1. The API will be available at `http://localhost:8000`
2. Use the setup endpoints to configure Chrome profile:
   ```bash
   curl -X POST http://localhost:8000/api/setup/test-connection
   ```
3. A browser window will open (if `BROWSER_HEADLESS=false`)
4. Manually log in to Google Flow UI
5. Cookies will be saved automatically for future use

### Development Mode

For development with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "profiles/*" --reload-exclude "output/*" --reload-exclude "logs/*" --reload-exclude "images/*" --reload-exclude "venv/*" --reload-exclude "chromedata/*" --reload-exclude "**/__pycache__/*"
```

The `--reload` flag enables automatic restart on code changes. Large directories are excluded from file watching to avoid OS file watch limit errors.

### Troubleshooting Installation

#### Python Version Issues

Check Python version:
```bash
python3 --version  # Should be 3.10 or higher
```

#### Playwright Installation Issues

If Playwright browsers fail to install:
```bash
playwright install --force chromium
```

#### Database Connection Issues

For SQLite (default):
- Ensure write permissions in the backend directory
- Check that `veoflow.db` file can be created

For PostgreSQL:
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection string format: `postgresql://user:password@host:port/database`
- Test connection: `psql -U user -d database`

#### Redis Connection Issues

Test Redis connection:
```bash
redis-cli ping  # Should return "PONG"
```

If Redis is not running:
```bash
# Linux
sudo systemctl start redis

# Mac (Homebrew)
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

#### FFmpeg Not Found

Install FFmpeg:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

## Features

- **Browser Automation**: Playwright-based automation for Google Flow UI
- **AI Integration**: Script generation using OpenAI/Anthropic/Gemini
- **Scene Management**: Scene breakdown and Veo Ultra prompt optimization
- **Character Consistency**: DNA-based character consistency system
- **Video Rendering**: Automated video generation through Flow UI
- **Video Processing**: FFmpeg-based video stitching with transitions
- **Job Queue**: Celery + Redis for async render processing

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Database models
│   ├── services/            # Core services
│   ├── api/                 # API endpoints
│   ├── workers/             # Celery workers
│   ├── utils/               # Utility functions
│   └── core/                # Core components
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── veoflow.config.json      # Application configuration
└── init_db.py              # Database initialization
```

## API Endpoints

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/generate-script` - Generate script
- `POST /api/projects/{id}/generate-script-from-parameters` - Generate script from parameters
- `POST /api/projects/{id}/stitch` - Stitch videos

### Scripts
- `GET /api/projects/{project_id}/script` - Get script for a project
- `PUT /api/projects/{project_id}/script` - Update script
- `DELETE /api/projects/{project_id}/script` - Delete script

### Scenes
- `GET /api/scenes?project_id={id}` - List scenes
- `POST /api/scenes` - Create scene
- `GET /api/scenes/{id}` - Get scene
- `PUT /api/scenes/{id}` - Update scene
- `DELETE /api/scenes/{id}` - Delete scene
- `POST /api/scenes/projects/{project_id}/generate-prompts` - Generate prompts for scenes

### Characters
- `GET /api/characters?project_id={id}` - List characters
- `POST /api/characters` - Create character
- `GET /api/characters/{id}` - Get character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character
- `POST /api/characters/projects/{project_id}/generate` - Generate characters from script

### Render
- `POST /api/render/scenes/{id}/render` - Start render for a scene
- `POST /api/render/projects/{id}/render-all` - Render all scenes in a project
- `GET /api/render/tasks/{task_id}` - Get task status
- `POST /api/render/scenes/{id}/cancel` - Cancel render

### Queue
- `GET /api/queue` - List active tasks
- `GET /api/queue/stats` - Queue statistics

### Setup
- `GET /api/setup/status` - Get setup status (Chrome profile, login status)
- `POST /api/setup/test-connection` - Test Google Flow connection
- `POST /api/setup/open-browser` - Open browser for manual login
- `GET /api/setup/chrome-profile` - Get Chrome profile information

#### Profile Management
- `POST /api/setup/profiles` - Create a new Chrome profile
- `GET /api/setup/profiles` - List all profiles
- `GET /api/setup/profiles/{profile_id}` - Get profile details
- `DELETE /api/setup/profiles/{profile_id}` - Delete profile
- `POST /api/setup/profiles/{profile_id}/set-active` - Set profile as active
- `POST /api/setup/profiles/{profile_id}/open` - Open browser with profile
- `POST /api/setup/profiles/{profile_id}/open-gmail` - Open Gmail login tab
- `POST /api/setup/profiles/{profile_id}/open-flow` - Open Flow login tab
- `GET /api/setup/profiles/{profile_id}/login-status` - Check login status
- `POST /api/setup/profiles/{profile_id}/confirm-login` - Confirm login and save cookies
- `POST /api/setup/profiles/{profile_id}/close` - Close browser for profile

### Logs
- `GET /api/logs` - Get application logs (with filters: level, logger_name, limit, since)
- `GET /api/logs/recent` - Get most recent logs
- `DELETE /api/logs` - Clear log buffer
- `GET /api/logs/file` - Get path to log file

## Development

### Quick Start for Development

1. Follow the [Building and Installation](#building-and-installation) steps above
2. Start the FastAPI server with reload:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "profiles/*" --reload-exclude "output/*" --reload-exclude "logs/*" --reload-exclude "images/*" --reload-exclude "venv/*" --reload-exclude "chromedata/*" --reload-exclude "**/__pycache__/*"
   ```
3. Start Celery worker in a separate terminal:
   ```bash
   celery -A app.workers.render_worker worker --loglevel=info
   ```
4. Access API documentation at `http://localhost:8000/docs`

### Development Workflow

1. **Make code changes** in the `app/` directory
2. **FastAPI auto-reloads** when using `--reload` flag
3. **Test endpoints** using the interactive docs at `/docs`
4. **Check logs** at `logs/veoflow_app.log` or via `/api/logs` endpoint

### Database Migrations

When modifying database models:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Structure

- `app/main.py` - FastAPI application entry point
- `app/api/` - API route handlers
- `app/models/` - SQLAlchemy database models
- `app/services/` - Business logic and service classes
- `app/workers/` - Celery task workers
- `app/core/` - Core utilities (database, logging, config)

For more detailed setup instructions, see `SETUP.md` in the parent directory.

## Configuration

Configuration is managed through:
1. Environment variables (`.env` file)
2. `veoflow.config.json` (application config)

Key settings:
- `OPENAI_API_KEY` - OpenAI API key for script generation
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection for Celery
- `FLOW_URL` - Google Flow project URL
- `BROWSER_HEADLESS` - Run browser in headless mode

## Testing

```bash
# Run tests (when implemented)
pytest tests/
```

## License

MIT

