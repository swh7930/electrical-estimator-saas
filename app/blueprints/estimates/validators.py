from typing import List, Any

def validate_fast_export_payload(payload: Any) -> List[str]:
    """
    Accept any of the following (dicts), either at the top level or under summary_export:
      - cells
      - totals
      - controls
    """
    if not isinstance(payload, dict):
        return ["payload: must be a JSON object"]

    se = payload.get("summary_export") if isinstance(payload.get("summary_export"), dict) else None

    def has_dict(root: dict, key: str) -> bool:
        return isinstance(root.get(key), dict)

    cells_ok = has_dict(payload, "cells") or (se is not None and has_dict(se, "cells"))
    totals_ok = has_dict(payload, "totals") or (se is not None and has_dict(se, "totals"))
    ctrls_ok = has_dict(payload, "controls") or (se is not None and has_dict(se, "controls"))

    return [] if (cells_ok or totals_ok or ctrls_ok) else ["cells or totals or controls: required object"]
