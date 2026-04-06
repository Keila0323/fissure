# ATO Risk Scorer

**AI-powered account takeover vulnerability analysis for banking and fintech recovery flows.**

Paste a description of your institution's account recovery process and get a risk score, severity-ranked vulnerability breakdown, lifecycle gap analysis, and specific remediation controls — powered by GPT-4o.

---

## Live Demo

| Deployment | URL |
|---|---|
| **Frontend (GitHub Pages)** | https://keila0323.github.io/ato-risk-scorer |
| **Backend API (Render)** | https://ato-risk-scorer.onrender.com |

---

## What It Does

Account recovery is the #1 ATO (Account Takeover) entry point — attackers exploit weaker recovery controls to bypass stronger onboarding protections. ATO Risk Scorer analyzes described recovery flows against known attack patterns and outputs:

- **Risk Score** (0–100) with tier classification (Critical / High / Moderate / Low)
- **Vulnerability Breakdown** — severity-ranked, each linked to a specific ATO attack vector
- **Lifecycle Gap Analysis** — across onboarding, recovery, dormancy, and offboarding
- **Priority Controls** — specific, actionable recommendations for each gap

---

## Key Attack Patterns Detected

- SIM-swap combined with phone-based OTP recovery
- OSINT-assisted Knowledge-Based Authentication (KBA) bypass
- Social engineering via customer support override
- Dormant account reactivation without step-up authentication
- Stale token and OAuth authorization persistence post-recovery
- Fragmented ownership gaps between fraud, product, compliance, and support

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.11 |
| AI Analysis | OpenAI GPT-4o |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Backend Hosting | Render |
| Frontend Hosting | GitHub Pages |

---

## Running Locally

```bash
git clone https://github.com/Keila0323/ato-risk-scorer.git
cd ato-risk-scorer
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

> **Note:** If no `OPENAI_API_KEY` is set, the app runs in mock mode and returns a representative sample analysis so the interface is fully functional.

---

## API

```
POST /api/analyze
Content-Type: application/json

{
  "flow_description": "Users reset via SMS OTP and KBA..."
}
```

Returns a structured JSON report with `risk_score`, `risk_tier`, `vulnerabilities[]`, `lifecycle_gaps`, and `controls_summary`.

```
GET /api/health
```

Returns `{ "status": "ok" }` — used for uptime monitoring.

---

## Project Background

This project emerged from research into identity lifecycle failures in financial services — specifically how fragmented ownership between product, security, fraud, and compliance teams creates exploitable gaps at every stage from onboarding through account deactivation.

Built for the **OpenAI × Handshake Codex Creator Challenge 2026**.

---

*Built by Keila Olaverria — B.S. Data Science & Analytics with Applied AI, Northeastern University | 12+ years banking and financial services*
