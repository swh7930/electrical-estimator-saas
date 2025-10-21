from typing import List, Any

def validate_fast_export_payload(payload: Any) -> List[str]:
    """
    HF2c.1: Accept either 'cells' (preferred) or 'totals' for Fast Export payloads.
    Requirements:
      - payload must be a JSON object (dict)
      - EITHER payload['cells'] is a dict OR payload['totals'] is a dict
    Returns:
      - [] when valid
      - list of "field: message" strings when invalid
    """
    errors: List[str] = []

    if not isinstance(payload, dict):
        return ["payload: must be a JSON object"]

    cells = payload.get("cells")
    totals = payload.get("totals")

    if not isinstance(cells, dict) and not isinstance(totals, dict):
        errors.append("cells or totals: required object")

    return errors
