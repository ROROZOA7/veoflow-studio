# VeoFlow Studio Backend

FastAPI backend for VeoFlow Studio video generation application.

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
- `POST /api/projects/{id}/stitch` - Stitch videos

### Scenes
- `GET /api/scenes?project_id={id}` - List scenes
- `POST /api/scenes` - Create scene
- `GET /api/scenes/{id}` - Get scene
- `PUT /api/scenes/{id}` - Update scene
- `DELETE /api/scenes/{id}` - Delete scene

### Characters
- `GET /api/characters?project_id={id}` - List characters
- `POST /api/characters` - Create character
- `GET /api/characters/{id}` - Get character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character

### Render
- `POST /api/render/scenes/{id}/render` - Start render
- `GET /api/render/tasks/{task_id}` - Get task status
- `POST /api/render/scenes/{id}/cancel` - Cancel render

### Queue
- `GET /api/queue` - List active tasks
- `GET /api/queue/stats` - Queue statistics

## Development

See `SETUP.md` for detailed setup instructions.

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

