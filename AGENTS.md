# Project Setup and Workflow

## Initial Setup
The project requires a virtual environment (`venv`) and specific dependencies.

1.  **Create venv:**
    *   **Linux/Mac:** `python3 -m venv venv`
    *   **Windows:** `python -m venv venv`
2.  **Activate venv:**
    *   **Linux/Mac:** `source venv/bin/activate`
    *   **Windows:** `venv\Scripts\activate`
3.  **Install Dependencies:**
    *   `pip install -r requirements.txt`
4.  **Environment:** Copy the sample environment file:
    *   `cp .env.sample .env`

## Running the Application
The main application entry point is via `run.py`.

*   **Local Run:** `python run.py`

## Deployment / Docker
For containerized deployment, use the provided `Dockerfile`:
*   `docker build -t mini-collaborator .`
*   `docker run -p 8000:8000 --env-file .env mini-collaborator`

## Notes
*   The application uses FastAPI, with core dependencies including `fastapi`, `uvicorn`, and `sqlalchemy`.
*   Always ensure the virtual environment is active before running development or test commands.