# Excel Intelligence Agent

Upload **any** Excel sheet (messy, structured, or unstructured) and get:

1. **A refined, cleaned table** (downloadable as `.xlsx`) with detected columns, types and data-quality notes.
2. **A knowledge document** — summary, data relationships, insights, anomalies, business context and recommendations.
3. **AI-suggested dashboards** — pick one or describe a **custom scenario**, and the agent builds a live ECharts dashboard.
4. **Natural-language Q&A** — ask questions about the data ("total sales by region") and get answers backed by real SQL queries.

## Architecture

| Piece | Tech |
|---|---|
| Backend | Python · FastAPI · pandas · openpyxl · DuckDB |
| LLM | Google Gemini (`google-generativeai`) |
| Frontend | Next.js (static export) · React · Tailwind · ECharts |
| Hosting | Render (see `render.yaml`) |

## Project layout

```
backend/
  app/
    main.py           # FastAPI routes
    excel_parser.py   # messy-Excel parsing + cleaning
    pipeline.py       # upload -> clean -> insights orchestration
    dashboard.py      # dashboard suggestion + spec/data generation
    qa.py             # text-to-SQL Q&A
    storage.py        # DuckDB + JSON persistence per dataset
    llm.py            # Gemini wrapper (graceful fallback)
    config.py         # env settings
  test_smoke.py       # end-to-end smoke test (no API key needed)
frontend/
  app/                # Next.js App Router (static export)
  components/         # Upload, table, insights, dashboards, chat
```

## Run locally

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
# open http://localhost:3000
```

### Environment variables
| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | No (fallback mode works) | Google AI Studio key. Enables smart structure inference, rich insights, dashboard design and Q&A. |
| `GEMINI_MODEL` | No | Default `gemini-2.0-flash`. |
| `CORS_ORIGINS` | No | Comma-separated allowed origins, default `*`. |
| `DATA_DIR` | No | Where datasets are stored. |

## Deploy on Render

The repo includes a **Render Blueprint** (`render.yaml`), so deployment is one click:

1. Push this repo to GitHub.
2. In Render, go to **New → Blueprint** and select the repo.
3. Render will create **two services**:
   - `excelagent-backend` (Python web service)
   - `excelagent-frontend` (static site)
4. Set the required **environment variables** (Render will prompt for the ones marked `sync: false`):
   - For **backend**: `GEMINI_API_KEY` (get one free at https://aistudio.google.com/apikey).
   - For **frontend**: `NEXT_PUBLIC_API_URL` = `https://<your-backend-service>.onrender.com` (the backend URL Render shows you).
5. Deploy. Open the frontend URL and upload a sheet.

> Tip: if `CORS_ORIGINS` is `*`, skip setting anything else — it works out of the box.

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/datasets/upload` | Upload `.xlsx/.xls/.csv`, returns cleaned dataset + preview |
| GET | `/api/datasets/{id}/table` | Paginated refined table |
| GET | `/api/datasets/{id}/download` | Download refined table as `.xlsx` |
| POST | `/api/datasets/{id}/insights` | Generate knowledge document |
| GET | `/api/datasets/{id}/insights` | Fetch knowledge document |
| POST | `/api/datasets/{id}/dashboards/suggest` | Suggest dashboards |
| POST | `/api/datasets/{id}/dashboards/build` | Build dashboard (by suggestion or custom scenario) |
| POST | `/api/datasets/{id}/chat` | Ask a question, get an answer + SQL table |
