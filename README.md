This is an end-to-end proof-of-concept DLP email classifier that behaves like a mini production system:

Model: Fine-tuned DistilBERT (dlp_model_distilbert-base) classifies emails as safe, sensitive, or critical.

API: Lightweight FastAPI service (/classify) returns probabilities, per-label scores, and a policy action:

≤ 0.5 → Send Normally

≤ 0.8 → Quarantine for Review

0.8 → Trash & Alert Security

Email Flow: An SMTP proxy (aiosmtpd) intercepts emails, calls the classifier, and applies the policy.

Sandbox: MailHog safely captures and displays emails (no external delivery).

UI: React + Vite frontend shows classification results and system actions, proxied via Nginx.

Deployment: Run everything locally or with Docker Compose (API, SMTP proxy, UI, MailHog).
