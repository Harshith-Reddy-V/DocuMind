# DocuMind Deployment Guide

This guide covers deploying the **DocuMind** application (FastAPI backend + React Vite frontend) to production hosting platforms.

---

## 1. Architecture & Deployment Model

- **Frontend**: React + TypeScript + Vite single-page application (SPA). Deploys to any static hosting provider with CDN (e.g., Vercel, Netlify, Render Static Site).
- **Backend**: FastAPI (Python 3.12) with Uvicorn, SQLite, ChromaDB, PyMuPDF, and Google GenAI SDK. Deploys to a Python web service (e.g., Render, Railway, Fly.io, or Docker).
- **AI Integration**: Google Gemini API (`gemini-2.5-flash` for generation/OCR and `text-embedding-004` for embeddings). The backend securely holds the `GEMINI_API_KEY`. **The API key is never sent or exposed to the frontend**.

---

## 2. Recommended Hosting Setup: Render + Vercel (or Render Blueprint)

| Component | Platform | Free Tier Availability | Cold Start / Sleep | Storage Model |
| :--- | :--- | :--- | :--- | :--- |
| **Backend** | **Render** (Web Service) | Yes ($0/month) | Spins down after 15 min idle; wakes in ~45–60s on first request | Ephemeral disk by default (resets on redeploy/spin-down). Persistent disk is a \$1/GB/mo add-on. |
| **Frontend** | **Vercel** or **Render Static** | Yes ($0/month) | Instant (Edge CDN, zero cold start) | Static distribution assets (`dist/`) |

---

## 3. Storage & Persistence Considerations

DocuMind uses three local storage directories:
1. `UPLOAD_DIR` (`./data/uploads`): Uploaded academic PDF files.
2. `VECTOR_DB_DIR` (`./data/chroma`): ChromaDB vector embeddings with cosine metric.
3. `DATABASE_URL` (`sqlite:///./data/documind.db`): SQLite database for metadata, status, and patent reports.

### Free-Tier Ephemeral Storage vs. Persistent Disk
- **On Free Tier Web Services (Render / Heroku)**: The container filesystem is ephemeral. If the service restarts or redeploys, documents and vector indices created in previous sessions reset to empty.
- **For Permanent Persistence**:
  - In Render, attach a **Persistent Disk** (e.g., mounted at `/data`, 1 GB).
  - Set the backend environment variables:
    ```env
    UPLOAD_DIR=/data/uploads
    VECTOR_DB_DIR=/data/chroma
    DATABASE_URL=sqlite:////data/documind.db
    ```
  - All uploaded documents, ChromaDB vectors, and patent reports will persist indefinitely across all restarts and deploys.

---

## 4. Option A: 1-Click Render Blueprint (Full Stack on Render)

The repository includes a ready-to-use [`render.yaml`](./render.yaml) blueprint specification that configures both the backend and frontend automatically.

### Steps:
1. Push your repository to GitHub.
2. Go to the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint**.
4. Connect your GitHub repository.
5. Render reads `render.yaml` and provisions two services:
   - `documind-backend` (Web Service)
   - `documind-frontend` (Static Site)
6. In the environment configuration screen, fill in:
   - `GEMINI_API_KEY`: Your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
7. Click **Apply**.
8. Once the backend finishes building, copy its URL (e.g., `https://documind-backend-xxxx.onrender.com`).
9. Update the frontend's environment variable:
   - `VITE_API_BASE_URL` = `https://documind-backend-xxxx.onrender.com`
10. Update the backend's `ALLOWED_ORIGINS`:
    - `ALLOWED_ORIGINS` = `https://documind-frontend-xxxx.onrender.com`
11. Redeploy both services.

---

## 5. Option B: Render (Backend) + Vercel (Frontend) [Recommended]

### Step 1: Deploy Backend on Render
1. Go to [Render Dashboard](https://dashboard.render.com) → **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `documind-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Add Environment Variables:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.12.5` | Pinned Python runtime |
   | `GEMINI_API_KEY` | `your_gemini_api_key` | Secret key from Google AI Studio |
   | `ALLOWED_ORIGINS` | `*` (or your Vercel URL once deployed) | Allowed CORS origins |
   | `GEMINI_GENERATION_MODEL` | `gemini-2.5-flash` | Generation & OCR model |
   | `GEMINI_EMBEDDING_MODEL` | `text-embedding-004` | Embedding model |
5. Click **Create Web Service**.
6. Verify deployment:
   - Root URL: `https://<backend-name>.onrender.com/` (returns JSON status)
   - Health check: `https://<backend-name>.onrender.com/api/health`
   - Interactive OpenAPI docs: `https://<backend-name>.onrender.com/docs`

---

### Step 2: Deploy Frontend on Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New...** → **Project**.
2. Import your GitHub repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click "Edit" and choose `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Expand **Environment Variables** and add:
   | Name | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://<backend-name>.onrender.com` |
5. Click **Deploy**.
6. Once deployed, copy your live frontend URL (e.g., `https://documind.vercel.app`).
7. Return to Render and update the backend's `ALLOWED_ORIGINS` to `https://documind.vercel.app`.

---

## 6. Option C: Docker Container Deployment

You can build and run DocuMind with Docker anywhere (e.g., Railway, Fly.io, Hugging Face, or local server):

```bash
# Build the Docker image
docker build -t documind-backend -f backend/Dockerfile backend

# Run the container with your Gemini key
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e ALLOWED_ORIGINS="http://localhost:5173" \
  -v documind_data:/app/data \
  --name documind \
  documind-backend
```

---

## 7. Verification Checklist

After deploying, verify the live deployment:
- [ ] **Health Endpoint**: `GET /api/health` returns status `"ok"` and `"gemini_key_configured": true`.
- [ ] **API Documentation**: `GET /docs` displays Swagger UI with all Document, Workspace, and Patent endpoints.
- [ ] **PDF Ingestion**: Upload an academic PDF via the frontend UI; verify processing progress bar reaches 100%.
- [ ] **Grounded Q&A**: Ask a question whose answer is in the document; verify response contains accurate page citations.
- [ ] **Exact Refusal**: Ask an out-of-document question; verify exact refusal sentence is returned.
- [ ] **Hierarchical Summarization**: Request short and detailed summaries.
- [ ] **Patent Feasibility Analyzer**: Enter an invention idea, attach a paper, and verify structured report generation and persistence.

---

## 8. Redeployment Workflow

Whenever you push new commits to your GitHub repository:
- **Render** automatically detects changes and triggers a rolling backend redeploy.
- **Vercel** automatically rebuilds and redeploys the frontend in seconds.
