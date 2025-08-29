import os
import hashlib
from typing import List, Dict, Optional

import torch
import torch.nn.functional as F
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --------- Config & Paths ---------
API_KEY = os.getenv("API_KEY", "DEMO_KEY")
SENSITIVE_LABEL_OVERRIDE = os.getenv("SENSITIVE_LABEL")  # e.g. "sensitive", "1", "toxic"

def resolve_model_path() -> str:
    # 1) Respect env if valid
    p = os.getenv("MODEL_PATH")
    if p and os.path.isdir(p):
        return p
    # 2) Try typical local paths relative to this file
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(here, "../../model/dlp_model_distilbert-base")),
        os.path.abspath(os.path.join(here, "../model/dlp_model_distilbert-base")),
        os.path.abspath(os.path.join(here, "model/dlp_model_distilbert-base")),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    raise RuntimeError("Model path not found. Set MODEL_PATH or put model in ../model/dlp_model_distilbert-base")

MODEL_PATH = resolve_model_path()

app = FastAPI(title="DLP Model API")

# CORS (so the UI never hits a CORS wall)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Schemas ---------
class AttachmentMeta(BaseModel):
    filename: str = ""
    size: Optional[int] = None
    mimetype: Optional[str] = None

class EmailIn(BaseModel):
    subject: str = ""
    body: str
    headers: Dict[str, str] = Field(default_factory=dict)
    attachments: List[AttachmentMeta] = Field(default_factory=list)

class ClassifyOut(BaseModel):
    label: str
    score: float  # sensitive probability
    scores: Dict[str, float]
    action: str
    rationale: Optional[List[str]] = None
    model_version: Optional[str] = None
    policy_version: str = "v1-thresholds-0.5-0.8"
    debug: Optional[Dict[str, str]] = None

class PolicyIn(BaseModel):
    score: float

# --------- Auth ---------
def _auth(x_api_key: Optional[str]):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# --------- Load HF model ---------
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
hf_model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True)
hf_model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
hf_model.to(device)

config = hf_model.config
# Normalize id2label
id2label = {}
try:
    raw = getattr(config, "id2label", {}) or {}
    id2label = {int(k): str(v) for k, v in (raw.items() if isinstance(raw, dict) else enumerate(raw))}
except Exception:
    pass

num_labels = getattr(config, "num_labels", None) or (len(id2label) if id2label else None)
problem_type = getattr(config, "problem_type", None)  # "single_label_classification", "multi_label_classification", "regression", or None
labels_list = [id2label.get(i, f"LABEL_{i}") for i in range(num_labels or 0)]

def _find_sensitive_index() -> Optional[int]:
    # 1) explicit override
    if SENSITIVE_LABEL_OVERRIDE:
        target = SENSITIVE_LABEL_OVERRIDE.lower()
        for i, name in id2label.items():
            if name.lower() == target:
                return int(i)
        # also allow numeric override ("1")
        if target.isdigit():
            return int(target)
    # 2) heuristic search
    for i, name in id2label.items():
        n = str(name).lower()
        if any(k in n for k in ["sensitive", "restricted", "confidential", "positive", "toxic"]):
            return int(i)
    # 3) common fallback
    if num_labels == 2:
        return 1
    if num_labels == 1:
        return 0
    return None

sensitive_idx = _find_sensitive_index()

# --------- Helpers ---------
def _email_concat(e: EmailIn) -> str:
    hdrs = " ".join([f"{k}:{v}" for k, v in (e.headers or {}).items()])
    atts = " ".join([a.filename for a in (e.attachments or []) if a and a.filename])
    return f"[HEADERS] {hdrs}\n[SUBJECT] {e.subject}\n[BODY]\n{e.body}\n[ATTACH] {atts}\n"

def _policy_action(score: float) -> str:
    if score <= 0.5:
        return "Send Normally"
    elif score <= 0.8:
        return "Quarantine for Review"
    else:
        return "Trash & Alert Security"

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def _infer_scores(logits: torch.Tensor) -> (Dict[str, float], float, str):
    """
    Returns:
      scores: dict[label] -> prob
      sensitive_score: float
      label: predicted label string
    Handles: single-logit (sigmoid), multi-class (softmax), multi-label (sigmoid per label).
    """
    # Ensure batch dim 1
    if logits.ndim == 1:
        logits = logits.unsqueeze(0)

    # Multi-label head
    if problem_type == "multi_label_classification":
        probs = torch.sigmoid(logits).squeeze(0).tolist()
        scores = {id2label.get(i, f"LABEL_{i}"): float(probs[i]) for i in range(len(probs))}
        # derive sensitive prob
        if sensitive_idx is not None and sensitive_idx < len(probs):
            sensitive_score = float(probs[sensitive_idx])
        else:
            sensitive_score = float(max(probs)) if probs else 0.0
        # top label for display
        top_i = int(torch.tensor(probs).argmax().item()) if probs else 0
        label = id2label.get(top_i, f"LABEL_{top_i}")
        return scores, sensitive_score, label

    # Single-logit (binary BCEWithLogitsLoss style)
    if logits.shape[-1] == 1 or (num_labels == 1):
        prob_pos = torch.sigmoid(logits.squeeze(-1)).item()
        sensitive_score = float(prob_pos)
        scores = {
            "non_sensitive": float(1.0 - prob_pos),
            "sensitive": float(prob_pos),
        }
        label = "sensitive" if prob_pos >= 0.5 else "non_sensitive"
        return scores, sensitive_score, label

    # Multi-class softmax
    probs = torch.softmax(logits, dim=-1).squeeze(0).tolist()
    scores = {id2label.get(i, f"LABEL_{i}"): float(probs[i]) for i in range(len(probs))}
    # pick predicted label
    top_i = int(torch.tensor(probs).argmax().item())
    label = id2label.get(top_i, f"LABEL_{top_i}")
    # sensitive score
    if sensitive_idx is not None and sensitive_idx < len(probs):
        sensitive_score = float(probs[sensitive_idx])
    else:
        # if labels are generic, treat top prob as sensitive score (conservative)
        sensitive_score = float(probs[top_i])
    return scores, sensitive_score, label

# --------- Routes ---------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "problem_type": problem_type,
        "num_labels": num_labels,
        "id2label": id2label,
        "sensitive_idx": sensitive_idx,
    }

@app.post("/classify", response_model=ClassifyOut)
def classify(email: EmailIn, x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)
    text = _email_concat(email)
    inputs = tokenizer(text, truncation=True, max_length=512, return_tensors="pt").to(device)
    with torch.no_grad():
        out = hf_model(**inputs)
        logits = out.logits

    scores, sensitive_score, label = _infer_scores(logits)
    action = _policy_action(sensitive_score)

    return ClassifyOut(
        label=label,
        score=sensitive_score,
        scores=scores,
        action=action,
        rationale=None,
        model_version=getattr(hf_model.config, "name_or_path", "unknown"),
        debug={
            "problem_type": str(problem_type),
            "sensitive_idx": str(sensitive_idx),
        },
    )

@app.post("/policy/apply")
def apply_policy(p: PolicyIn, x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)
    return {"action": _policy_action(float(p.score))}
