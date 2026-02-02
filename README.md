# Laravel Docker Manager

A small developer tool that creates and manages a Docker-based
Laravel development environment with nginx, MySQL, phpMyAdmin,
and Mailpit.

Designed to replace or migrate away from Laravel Sail and
remove common Docker-on-Windows pain points.

## Features

- One-click Docker setup for existing Laravel projects
- Automatic nginx, PHP-FPM, MySQL, phpMyAdmin, and Mailpit setup
- Safe filesystem validation before Docker runs
- Detection and neutralization of Laravel Sail remnants
- Controlled database migrations and seeding
- Streamlit UI with explicit side effects (no accidental reruns)

## Why this exists

Laravel + Docker on Windows often fails due to:
- volume mount mismatches
- leftover Sail configuration
- container name collisions
- database startup races

This tool makes those failures explicit and preventable.

## Requirements

- Docker Desktop
- Python 3.11+
- Streamlit

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
