# 暮雨动画 v0 Project Setup

## Backend (FastAPI)

1.  Navigate to `backend` directory:
    ```bash
    cd backend
    ```
2.  Install dependencies (if not already):
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `fastapi`, `uvicorn`, `httpx` are in `requirements.txt`. I'll check this next)*
3.  Run the server:
    ```bash
    python main.py
    ```
    The API will be available at `http://localhost:8800`.

## Frontend (Vue 3 + Vite)

1.  Navigate to `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
4.  Open your browser at `http://localhost:3000`.

## Features

*   **Home:** Avant-garde dark theme with a large hero banner and poster grid.
*   **Detail:** Series page listing all episodes. Movie page with direct play.
*   **Player:** Integrated `Artplayer` for streaming.
