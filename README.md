# DLP Email Classifier Demo (SMTP Proxy → FastAPI → React UI)

This repo provides a **fully working demo** for your DLP classifier with:
- **FastAPI** backend wrapping your fine-tuned `dlp_model_distilbert-base`.
- **SMTP proxy** that classifies inbound email and routes it per policy.
- **React (Vite) UI** to paste an email and see label, score, and action.
- **MailHog** for safe email capture (no external delivery).

> **Policy mapping (as requested)**  
> If `score <= 0.5` → **Send Normally**  
> Else if `score <= 0.8` → **Quarantine for Review**  
> Else → **Trash & Alert Security**

---

## 0) Quick Start (Docker, recommended)

1) Put your **fine-tuned model folder** here:
```
./model/dlp_model_distilbert-base/
```

2) Copy `.env.example` to `.env` (or keep defaults):
```
cp .env.example .env
```

3) Build & run all services:
```
docker compose up --build
```

4) Open the UI:
- UI: http://localhost:8080
- MailHog (captures sent emails): http://localhost:8025
- API health: http://localhost:8000/health

---

## 1) Local Dev (no Docker)

### Backend (API)
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r api/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Put model into ./model/dlp_model_distilbert-base then run:
export MODEL_PATH=$(pwd)/model/dlp_model_distilbert-base
export API_KEY=DEMO_KEY
uvicorn app.main:app --app-dir api --host 0.0.0.0 --port 8000
```

### SMTP Proxy
```
source .venv/bin/activate
pip install -r gateway/requirements.txt
export API_URL=http://localhost:8000
export API_KEY=DEMO_KEY
export RELAY_HOST=localhost
export RELAY_PORT=1025
python gateway/smtp_proxy.py
```

### MailHog (captures mail)
- macOS: `brew install mailhog && mailhog`
- Linux/Windows: use Docker: `docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog`

### UI (Vite dev server with API proxy)
```
cd ui
npm ci
npm run dev
# Vite will open http://localhost:5173 (UI will proxy /api to http://localhost:8000)
```

---

## 2) Directory Structure

```
dlp-demo/
├─ api/
│  ├─ app/
│  │  ├─ __init__.py
│  │  └─ main.py
│  ├─ requirements.txt
│  └─ Dockerfile
├─ gateway/
│  ├─ smtp_proxy.py
│  ├─ requirements.txt
│  └─ Dockerfile
├─ model/
│  └─ dlp_model_distilbert-base/   # <-- place your fine-tuned HF model here
├─ ui/
│  ├─ src/
│  │  ├─ App.jsx
│  │  ├─ main.jsx
│  │  ├─ components/
│  │  │  ├─ ClassifierForm.jsx
│  │  │  ├─ MetricPill.jsx
│  │  │  └─ ResultCard.jsx
│  │  └─ styles.css
│  ├─ index.html
│  ├─ package.json
│  ├─ package-lock.json
│  ├─ vite.config.js
│  └─ Dockerfile
├─ .env.example
├─ docker-compose.yml
├─ scripts/
│  ├─ send_test.py
│  └─ sample_email.txt
└─ README.md
```

---

## 3) Test the SMTP Proxy

With everything up via Docker compose, run:
```
python scripts/send_test.py
```
Then check MailHog at http://localhost:8025

---

## 4) Notes

- API expects the model at `MODEL_PATH` (`/models/dlp_model_distilbert-base` in Docker). In Docker, we volume-mount `./model` to `/models`.
- The UI uses **Nginx** to serve static files and **proxy `/api`** to the FastAPI container, so no CORS pain.
- Policy action is returned by the API and also re-evaluated server-side for the SMTP proxy.
- Keep this repository offline-friendly by placing the model locally.
