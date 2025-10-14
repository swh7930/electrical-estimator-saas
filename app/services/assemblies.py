from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from app.extensions import db
from app.models.assembly import Assembly, AssemblyComponent
from app.models.material import Material
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func


def _to_int_or_default(value, default=1):
    try:
        v = int(value or 0)
        return v if v > 0 else default
    except Exception:
        return default


def _to_decimal(value):
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def get_assembly_rollup(assembly_id: int) -> dict:
    """
    Compute live totals for an assembly:
      - material_cost_total: SUM(qty_per_assembly * price_each)
      - labor_hours_total:   SUM(qty_per_assembly * labor_each)

    price_each  = Material.price      / unit_quantity_size
    labor_each  = Material.labor_unit / unit_quantity_size

    Returns a dict with Decimal totals quantized to 4 places.
    """
    rows = (
        db.session.query(
            AssemblyComponent.qty_per_assembly,
            Material.price,
            Material.labor_unit,
            Material.unit_quantity_size,
        )
        .join(Material, Material.id == AssemblyComponent.material_id)
        .filter(AssemblyComponent.assembly_id == assembly_id)
        .filter(AssemblyComponent.is_active == True)
        .all()
    )

    material_total = Decimal("0")
    labor_total = Decimal("0")
    count = 0

    for qty, price, labor_unit, unit_qty in rows:
        count += 1
        u = _to_int_or_default(unit_qty, default=1)
        price_each = _to_decimal(price) / Decimal(u)
        labor_each = _to_decimal(labor_unit) / Decimal(u)

        q = _to_decimal(qty)
        material_total += q * price_each
        labor_total += q * labor_each

    # round to 4 decimals (consistent with NUMERIC(12,4))
    q4 = lambda d: d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    return {
        "assembly_id": assembly_id,
        "material_cost_total": q4(material_total),
        "labor_hours_total": q4(labor_total),
        "component_count": count,
    }


class ServiceError(RuntimeError):
    """Recoverable service error (validation/uniqueness/etc.)."""


@dataclass(frozen=True)
class Page:
    items: List
    total: int
    limit: int
    offset: int


def get_assembly(
    session: Session, assembly_id: int, *, include_inactive: bool = True
) -> Assembly:
    q = session.query(Assembly).filter(Assembly.id == assembly_id)
    if not include_inactive:
        q = q.filter(Assembly.is_active.is_(True))
    obj = q.one_or_none()
    if not obj:
        raise ServiceError(f"Assembly {assembly_id} not found")
    return obj


def list_assemblies(
    session: Session,
    *,
    active_only: bool = True,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Page:
    query = session.query(Assembly)
    if active_only:
        query = query.filter(Assembly.is_active.is_(True))
    if category:
        query = query.filter(func.lower(Assembly.category) == func.lower(category))
    if subcategory:
        query = query.filter(
            func.lower(Assembly.subcategory) == func.lower(subcategory)
        )
    if q:
        like = f"%{q.strip().lower()}%"
        query = query.filter(func.lower(Assembly.name).like(like))
    total = query.count()
    items = (
        query.order_by(
            func.lower(Assembly.category).nullsfirst(), func.lower(Assembly.name)
        )
        .limit(limit)
        .offset(offset)
        .all()
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


def create_assembly(
    session: Session,
    *,
    name: str,
    notes: Optional[str] = None,
    assembly_code: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    is_featured: bool = False,
) -> Assembly:
    if not name or not name.strip():
        raise ServiceError("Name is required.")
    asm = Assembly(
        name=name.strip(),
        notes=(notes or None),
        assembly_code=(assembly_code or None),
        category=(category or None),
        subcategory=(subcategory or None),
        is_featured=bool(is_featured),
    )
    session.add(asm)
    try:
        session.flush()  # enforce unique/constraints early
    except IntegrityError as e:
        session.rollback()
        raise ServiceError("Duplicate active assembly name.") from e
    return asm


def update_assembly(
    session: Session,
    assembly_id: int,
    *,
    name: Optional[str] = None,
    notes: Optional[str] = None,
    assembly_code: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    is_featured: Optional[bool] = None,
) -> Assembly:
    asm = get_assembly(session, assembly_id)
    if name is not None:
        if not name.strip():
            raise ServiceError("Name cannot be blank.")
        asm.name = name.strip()
    if notes is not None:
        asm.notes = notes or None
    if assembly_code is not None:
        asm.assembly_code = assembly_code or None
    if category is not None:
        asm.category = category or None
    if subcategory is not None:
        asm.subcategory = subcategory or None
    if is_featured is not None:
        asm.is_featured = bool(is_featured)
    asm.updated_at = func.now()
    try:
        session.flush()
    except IntegrityError as e:
        session.rollback()
        raise ServiceError("Duplicate active assembly name.") from e
    return asm


def set_assembly_active(session: Session, assembly_id: int, active: bool) -> Assembly:
    asm = get_assembly(session, assembly_id)
    asm.is_active = bool(active)
    asm.updated_at = func.now()
    session.flush()
    return asm


def hard_delete_assembly(session: Session, assembly_id: int) -> None:
    asm = get_assembly(session, assembly_id)
    session.delete(asm)
    try:
        session.flush()
    except IntegrityError as e:
        session.rollback()
        raise ServiceError(
            "Assembly cannot be deleted (has components or is referenced)."
        ) from e


def list_components(
    session: Session, assembly_id: int, *, include_inactive: bool = False
) -> List[AssemblyComponent]:
    q = session.query(AssemblyComponent).filter(
        AssemblyComponent.assembly_id == assembly_id
    )
    if not include_inactive:
        q = q.filter(AssemblyComponent.is_active.is_(True))
    return q.order_by(
        AssemblyComponent.sort_order.nullsfirst(), AssemblyComponent.id
    ).all()


def add_component(
    session: Session,
    *,
    assembly_id: int,
    material_id: int,
    qty_per_assembly: float,
    sort_order: Optional[int] = None,
) -> AssemblyComponent:
    # Ensure parent + material exist
    get_assembly(session, assembly_id)
    mat = session.query(Material).filter(Material.id == material_id).one_or_none()
    if not mat:
        raise ServiceError(f"Material {material_id} not found.")
    comp = AssemblyComponent(
        assembly_id=assembly_id,
        material_id=material_id,
        qty_per_assembly=qty_per_assembly,
        sort_order=sort_order,
    )
    try:
        session.add(comp)
        session.flush()  # unique index (assembly_id, material_id, active=true)
    except IntegrityError as e:
        session.rollback()
        raise ServiceError("Component already exists on this assembly (active).") from e
    return comp


def update_component(
    session: Session,
    component_id: int,
    *,
    qty_per_assembly: Optional[float] = None,
    sort_order: Optional[int] = None,
) -> AssemblyComponent:
    comp = (
        session.query(AssemblyComponent)
        .filter(AssemblyComponent.id == component_id)
        .one_or_none()
    )
    if not comp:
        raise ServiceError(f"Component {component_id} not found.")
    if qty_per_assembly is not None:
        comp.qty_per_assembly = qty_per_assembly
    if sort_order is not None:
        comp.sort_order = sort_order
    comp.updated_at = func.now()
    session.flush()
    return comp


def set_component_active(
    session: Session, component_id: int, active: bool
) -> AssemblyComponent:
    comp = (
        session.query(AssemblyComponent)
        .filter(AssemblyComponent.id == component_id)
        .one_or_none()
    )
    if not comp:
        raise ServiceError(f"Component {component_id} not found.")
    comp.is_active = bool(active)
    comp.updated_at = func.now()
    session.flush()
    return comp
