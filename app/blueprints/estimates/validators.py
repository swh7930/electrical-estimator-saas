from typing import List, Dict, Any

def validate_fast_export_payload(payload: Any) -> List[str]:
    """
    Minimal HF1 validation for Fast Export payloads.
    Requirements:
      - payload must be an object (dict)
      - payload["totals"] must exist and be an object (dict)
    Return:
      - [] when valid
      - list of "field: message" strings when invalid
    """
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["payload: must be a JSON object"]
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        errors.append("totals: required object")
    return errors
