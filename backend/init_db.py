"""
Initialize database - Create tables
"""

from app.core.database import init_db, engine
from app.core.logging_config import setup_logging
import logging

setup_logging("INFO")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")

