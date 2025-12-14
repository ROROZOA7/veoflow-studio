# VeoFlow Studio

A full-stack video generation application that automates Google Veo 3 Ultra video creation through browser automation.

## Overview

VeoFlow Studio enables users to generate videos by:
1. Providing a text prompt
2. AI generates a script and breaks it into scenes
3. Characters are defined with consistency DNA
4. Scenes are automatically rendered using Google Flow UI
5. Videos are stitched together with transitions

## Architecture

- **Backend**: Python + FastAPI
- **Frontend**: Next.js 14+ with TypeScript
- **Browser Automation**: Playwright
- **Job Queue**: Celery + Redis
- **Database**: PostgreSQL (or SQLite for development)
- **Video Processing**: FFmpeg

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or SQLite)
- Redis
- FFmpeg
- Chrome/Chromium

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Set up backend (see `backend/README.md`)
4. Set up frontend (see `frontend/README.md`)
5. Start services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Project Structure

```
veoflow-studio/
├── backend/          # Python FastAPI backend
├── frontend/         # Next.js frontend
├── output/           # Generated videos
├── projects/         # Project metadata
├── chromedata/       # Browser profile
└── temp/             # Temporary files
```

## Documentation

See `APPLICATION_DESIGN.md` for complete architecture and design documentation.

## License

MIT

