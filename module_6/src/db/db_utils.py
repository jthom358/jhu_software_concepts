"""Shared PostgreSQL utilities for the GradCafe application."""

from __future__ import annotations

import os
from typing import Any

import psycopg
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_database_url(database_url: str | None = None) -> str:
    """Return a PostgreSQL connection URL from an argument or environment variables."""
    if database_url:
        return database_url

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    if db_name and db_user:
        password_part = f":{db_password}" if db_password else ""
        return f"postgresql://{db_user}{password_part}@{db_host}:{db_port}/{db_name}"

    raise RuntimeError("DATABASE_URL or DB_NAME/DB_USER database settings are required.")


def connect(database_url: str | None = None) -> Any:
    """Create a psycopg connection using DATABASE_URL-compatible settings."""
    return psycopg.connect(get_database_url(database_url))
