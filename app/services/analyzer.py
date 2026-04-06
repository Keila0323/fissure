import os
import json
from openai import OpenAI

# Client is initialized lazily to allow startup without a key (mock fallback)
_client = None

def _get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        _client = OpenAI(api_key=key)
    return _client

SYSTEM_PROMPT = """You are a senior identity security architect specializing in Account Takeover (ATO) detection within banking and fintech environments.

Your task is to analyze a described account recovery or identity lifecycle flow and identify vulnerabilities that attackers could exploit to take over user accounts.

You must return ONLY valid JSON in the following structure — no markdown, no explanation, just JSON:

{
  "risk_score": <integer 0-100>,
  "risk_tier": "<Critical|High|Moderate|Low>",
  "summary": "<2-3 sentence executive summary of the overall risk posture>",
  "vulnerabilities": [
    {
      "id": "<short-id like VUL-01>",
      "title": "<vulnerability name>",
      "severity": "<Critical|High|Moderate|Low>",
      "pattern": "<the specific ATO attack pattern this enables>",
      "description": "<detailed explanation of the vulnerability and how it can be exploited>",
      "recommendation": "<specific, actionable control recommendation>"
    }
  ],
  "controls_summary": [
    "<short control recommendation 1>",
    "<short control recommendation 2>",
    "<short control recommendation 3>"
  ],
  "lifecycle_gaps": {
    "onboarding": "<brief assessment or null>",
    "recovery": "<brief assessment or null>",
    "dormancy": "<brief assessment or null>",
    "offboarding": "<brief assessment or null>"
  }
}

Risk score guidance:
- 80-100: Critical — multiple severe vulnerabilities, easy ATO paths
- 60-79: High — significant gaps, requires urgent remediation
- 40-59: Moderate — several medium gaps, attention needed
- 20-39: Low — minor gaps, strong baseline controls
- 0-19: Minimal — robust controls, few to no gaps

Identify 3-6 specific vulnerabilities. Be specific, technical, and actionable. Draw on real ATO tactics like:
- SIM-swapping combined with weak phone-based recovery
- Social engineering customer support to bypass controls
- Credential stuffing aided by predictable KBA questions
- Dormant account reactivation without re-authentication
- Insecure direct object references in reset flows
- Insufficient step-up authentication during high-risk actions
- Fragmented ownership leading to gap between fraud, product, and compliance teams
- Inadequate deactivation (lingering OAuth tokens, API keys, linked accounts)"""


def _mock_response(flow_text: str) -> dict:
    """Deterministic mock when OpenAI quota is unavailable."""
    score = 67
    # vary score based on text length as a simple proxy
    word_count = len(flow_text.split())
    if word_count < 50:
        score = 74
    elif word_count > 200:
        score = 55

    return {
        "risk_score": score,
        "risk_tier": "High",
        "summary": (
            "The described recovery flow exhibits multiple high-severity vulnerabilities "
            "that create exploitable pathways for account takeover. Phone-based verification "
            "without SIM-swap protection and weak knowledge-based authentication are the most "
            "critical gaps. Immediate remediation of authentication controls is recommended."
        ),
        "vulnerabilities": [
            {
                "id": "VUL-01",
                "title": "Phone-Based Recovery Without SIM-Swap Protection",
                "severity": "Critical",
                "pattern": "SIM-Swap + OTP Interception",
                "description": (
                    "Recovery flows that send OTPs or magic links to phone numbers are critically "
                    "vulnerable to SIM-swapping. Attackers socially engineer mobile carriers to "
                    "transfer victim numbers, then intercept all SMS-based verification. Without "
                    "SIM-swap detection (e.g., carrier API checks, recent number port alerts), "
                    "this provides a reliable ATO path."
                ),
                "recommendation": (
                    "Integrate carrier-level SIM-swap detection APIs (Telesign, Vonage Verify) "
                    "before sending any SMS OTP. Block recovery via phone for accounts flagged "
                    "with recent number porting activity. Offer TOTP authenticator as default."
                ),
            },
            {
                "id": "VUL-02",
                "title": "Knowledge-Based Authentication (KBA) as Primary Verification",
                "severity": "High",
                "pattern": "OSINT-Assisted Social Engineering",
                "description": (
                    "Static KBA questions (mother's maiden name, first pet, high school) are "
                    "trivially defeated via social media OSINT, data broker sites, and previous "
                    "breach data. Attackers systematically collect this information before "
                    "targeting recovery flows, achieving high success rates against KBA-reliant systems."
                ),
                "recommendation": (
                    "Eliminate static KBA entirely. Replace with dynamic KBA using transactional "
                    "history (e.g., 'Which of these merchants did you pay last month?') or "
                    "document-based identity verification (ID + selfie match) for high-value accounts."
                ),
            },
            {
                "id": "VUL-03",
                "title": "Dormant Account Reactivation Without Step-Up Authentication",
                "severity": "High",
                "pattern": "Dormant Identity Exploitation",
                "description": (
                    "Accounts inactive for 90+ days that can be reactivated through the same "
                    "recovery flow as active accounts represent a high-risk gap. Attackers target "
                    "dormant accounts because owners are less likely to notice suspicious activity, "
                    "and security controls may have weakened (e.g., expired MFA devices, old "
                    "phone numbers). The Synapse/Yotta collapse in 2024 exposed similar dormant "
                    "identity management failures at scale."
                ),
                "recommendation": (
                    "Implement a mandatory re-verification step for accounts dormant 90+ days: "
                    "require government ID re-submission or video selfie match. Send multi-channel "
                    "alerts (email + push) upon reactivation. Consider a 24-hour cooling period "
                    "before full fund access is restored."
                ),
            },
            {
                "id": "VUL-04",
                "title": "Support Channel Bypass (Social Engineering via Customer Service)",
                "severity": "High",
                "pattern": "Vishing / Authorized Push via Support",
                "description": (
                    "Customer support representatives with override capabilities represent a "
                    "significant ATO vector. Attackers impersonate account holders using "
                    "partial PII harvested from breaches, manipulating agents into resetting "
                    "credentials or disabling MFA. Fragmented ownership between fraud, product, "
                    "and compliance teams often leaves support agents with excessive permissions."
                ),
                "recommendation": (
                    "Enforce strict agent authorization: no identity changes without out-of-band "
                    "customer confirmation via registered email. Implement agent action logging "
                    "with anomaly detection on high-risk operations. Require dual-agent approval "
                    "for account recovery overrides. Conduct regular social engineering red-team exercises."
                ),
            },
            {
                "id": "VUL-05",
                "title": "Insufficient Token Invalidation on Account Recovery",
                "severity": "Moderate",
                "pattern": "Session Hijacking Post-Recovery",
                "description": (
                    "Recovery flows that reset passwords but fail to invalidate all active "
                    "sessions, OAuth tokens, API keys, and linked third-party app authorizations "
                    "leave attackers with persistent access even after victims reclaim accounts. "
                    "This is especially dangerous for fintech accounts with open banking "
                    "integrations and linked payment authorizations."
                ),
                "recommendation": (
                    "On any credential reset or recovery event: invalidate ALL active sessions, "
                    "revoke all OAuth authorizations, expire all API keys, and notify the user "
                    "of each revoked connection. Maintain a cryptographic audit log of "
                    "all token lifecycle events."
                ),
            },
        ],
        "controls_summary": [
            "Deploy SIM-swap detection at all phone-based verification touchpoints",
            "Replace KBA with dynamic transaction-based verification or biometric identity proofing",
            "Implement mandatory step-up authentication for dormant account reactivation",
        ],
        "lifecycle_gaps": {
            "onboarding": "Identity proofing strength at onboarding directly determines attack surface at recovery — weak onboarding KYC creates downstream recovery vulnerabilities.",
            "recovery": "Primary risk concentration: phone-based OTP and KBA gaps create reliable ATO entry points with readily available attacker tooling.",
            "dormancy": "Dormant accounts with stale contact information and weakened authentication posture are disproportionately targeted.",
            "offboarding": "Token and authorization cleanup at deactivation or closure is often incomplete, creating residual access paths.",
        },
    }


def analyze_flow(flow_text: str) -> dict:
    """Call GPT-4o to analyze an account recovery flow. Falls back to mock on quota errors."""
    client = _get_client()
    if client is None:
        return _mock_response(flow_text)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this account recovery/identity lifecycle flow for ATO vulnerabilities:\n\n{flow_text}",
                },
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        error_str = str(e).lower()
        if "insufficient_quota" in error_str or "rate_limit" in error_str or "quota" in error_str:
            return _mock_response(flow_text)
        raise e
