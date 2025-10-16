from typing import List, Dict
from app.utils.helpers import safe_float, round_currency

def calc_line(item_description, quantity, price, labor_hours, hourly_rate):
    qty  = safe_float(quantity, 0)
    cost = safe_float(price, 0)
    lhpu = safe_float(labor_hours, 0)  # labor hours per unit
    rate = safe_float(hourly_rate, 0)

    material_total       = qty * cost
    labor_total_hours    = qty * lhpu
    labor_total_dollars  = labor_total_hours * rate
    line_total           = material_total + labor_total_dollars
    return {
        "item_description": item_description,
        "quantity": qty,
        "price": cost,
        "labor_hours": lhpu,
        "material_total": material_total,
        "labor_total": labor_total_hours,
        "line_total": line_total
    }

def calc_totals(lines: List[Dict], hourly_rate: float):
    rate = safe_float(hourly_rate, 0)
    total_material = sum(safe_float(line.get("material_total"), 0) for line in lines)
    total_labor_h  = sum(safe_float(line.get("labor_total"), 0) for line in lines)
    return {
        "material_total": total_material,
        "labor_total": total_labor_h * rate,
        "grand_total": total_material + (total_labor_h * rate),
    }

# --- Step C (Summary): material adders ---
def material_adders(base_material_cost: float, misc: int, small: int, large: int, waste: int, tax: int):
    base  = safe_float(base_material_cost, 0)
    misc_v   = base * (safe_float(misc, 0)   / 100.0)
    small_v  = base * (safe_float(small, 0)  / 100.0)
    large_v  = base * (safe_float(large, 0)  / 100.0)
    waste_v  = base * (safe_float(waste, 0)  / 100.0)
    taxable  = base + misc_v + small_v + large_v + waste_v
    tax_v    = taxable * (safe_float(tax, 0) / 100.0)
    total    = taxable + tax_v
    return dict(
        misc=misc_v, small_tools=small_v, large_tools=large_v, waste_theft=waste_v,
        taxable=taxable, sales_tax=tax_v, total_material=total
    )

# --- Step F (Overhead) ---
def overhead_value(prime_cost: float, overhead_percent: int) -> float:
    return safe_float(prime_cost, 0) * (safe_float(overhead_percent, 0) / 100.0)

# --- Step H/I (Margin & Sales Price): "margin" is profit margin, not markup ---
def margin_to_markup(margin_percent: int) -> float:
    m = safe_float(margin_percent, 0) / 100.0
    if m >= 1:  # guard rails
        return 2.0
    return round(1.0 / (1.0 - m), 2)

def estimated_sales_price(break_even: float, margin_percent: int) -> float:
    return safe_float(break_even, 0) * margin_to_markup(margin_percent)
