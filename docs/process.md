# This document contains the step by step process carried out to set up the backend folder

## Step 1: create virtual environment

- Created virtual environment using uv
- To use this project's venv use the following command:
        uv init
            (if uv not present, type: "pip install uv")
        uv sync
        
        To activate:
            For windows:
                .venv\Scripts\activate
            For Linux:
                source .venv/bin/activate

## Step 2: database and env setup

- Installed packages:
        uv add fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary python-dotenv

- Added `.env` and `.env.example`:
        DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stocksense_db
        SECRET_KEY=your_secret_key_here

- Created `app/database.py` with SQLAlchemy connection and session handling.
- Created `app/main.py` for FastAPI server entry point.
