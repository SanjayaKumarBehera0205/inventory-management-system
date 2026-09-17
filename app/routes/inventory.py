import math
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Category, MovementType, Product, StockMovement, Supplier, User
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    DashboardRead,
    MovementCreate,
    MovementRead,
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductUpdate,
    SupplierCreate,
    SupplierRead,
)

router = APIRouter(tags=["Inventory"])


def commit_or_conflict(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=message)


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    category = Category(**payload.model_dump())
    db.add(category)
    commit_or_conflict(db, "Category name already exists")
    db.refresh(category)
    return category


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(Category).order_by(Category.name)))


@router.post("/suppliers", response_model=SupplierRead, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    commit_or_conflict(db, "Supplier name already exists")
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(Supplier).order_by(Supplier.name)))


def validate_relations(category_id: int | None, supplier_id: int | None, db: Session) -> None:
    if category_id is not None and db.get(Category, category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if supplier_id is not None and db.get(Supplier, supplier_id) is None:
        raise HTTPException(status_code=404, detail="Supplier not found")


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    validate_relations(payload.category_id, payload.supplier_id, db)
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.flush()
        if product.quantity:
            db.add(StockMovement(
                product_id=product.id,
                type=MovementType.STOCK_IN,
                quantity=product.quantity,
                previous_quantity=0,
                new_quantity=product.quantity,
                note="Opening stock",
                created_by=current_user.id,
            ))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product SKU already exists")
    db.refresh(product)
    return product


@router.get("/products", response_model=ProductPage)
def list_products(
    search: str | None = Query(default=None, max_length=200),
    category_id: int | None = None,
    supplier_id: int | None = None,
    low_stock: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Product.name.ilike(term), Product.sku.ilike(term)))
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if supplier_id is not None:
        filters.append(Product.supplier_id == supplier_id)
    if low_stock:
        filters.append(Product.quantity <= Product.reorder_level)
    total = db.scalar(select(func.count()).select_from(Product).where(*filters)) or 0
    items = list(db.scalars(
        select(Product).where(*filters).order_by(Product.name).offset((page - 1) * page_size).limit(page_size)
    ))
    return ProductPage(items=items, total=total, page=page, page_size=page_size, pages=math.ceil(total / page_size) if total else 0)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    values = payload.model_dump(exclude_unset=True)
    validate_relations(values.get("category_id", product.category_id), values.get("supplier_id", product.supplier_id), db)
    for field, value in values.items():
        setattr(product, field, value)
    commit_or_conflict(db, "Product SKU already exists")
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return Response(status_code=204)


@router.post("/stock-movements", response_model=MovementRead, status_code=201)
def create_movement(payload: MovementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.type in (MovementType.STOCK_IN, MovementType.STOCK_OUT) and payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    previous = product.quantity
    if payload.type == MovementType.STOCK_IN:
        new_quantity = previous + payload.quantity
    elif payload.type == MovementType.STOCK_OUT:
        new_quantity = previous - payload.quantity
    else:
        if payload.quantity < 0:
            raise HTTPException(status_code=400, detail="Adjusted stock cannot be negative")
        new_quantity = payload.quantity
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    product.quantity = new_quantity
    movement = StockMovement(
        **payload.model_dump(), previous_quantity=previous, new_quantity=new_quantity, created_by=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/stock-movements", response_model=list[MovementRead])
def list_movements(
    product_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(StockMovement)
    if product_id is not None:
        query = query.where(StockMovement.product_id == product_id)
    return list(db.scalars(query.order_by(StockMovement.created_at.desc()).limit(limit)))


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_products = db.scalar(select(func.count()).select_from(Product)) or 0
    total_units = db.scalar(select(func.coalesce(func.sum(Product.quantity), 0))) or 0
    total_value = db.scalar(select(func.coalesce(func.sum(Product.price * Product.quantity), 0))) or Decimal("0")
    low_stock = db.scalar(select(func.count()).select_from(Product).where(Product.quantity <= Product.reorder_level)) or 0
    out_of_stock = db.scalar(select(func.count()).select_from(Product).where(Product.quantity == 0)) or 0
    total_suppliers = db.scalar(select(func.count()).select_from(Supplier)) or 0
    recent = list(db.scalars(select(StockMovement).order_by(StockMovement.created_at.desc()).limit(5)))
    return DashboardRead(
        total_products=total_products,
        total_units=total_units,
        total_inventory_value=total_value,
        low_stock_products=low_stock,
        out_of_stock_products=out_of_stock,
        total_suppliers=total_suppliers,
        recent_movements=recent,
    )
