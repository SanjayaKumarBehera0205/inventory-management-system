from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import MovementType


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class CategoryRead(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    contact_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class SupplierRead(SupplierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal = Field(ge=0, decimal_places=2)
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)
    category_id: int | None = None
    supplier_id: int | None = None


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    reorder_level: int | None = Field(default=None, ge=0)
    category_id: int | None = None
    supplier_id: int | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: str | None
    price: Decimal
    quantity: int
    reorder_level: int
    category_id: int | None
    supplier_id: int | None
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
    pages: int


class MovementCreate(BaseModel):
    product_id: int
    type: MovementType
    quantity: int
    note: str | None = Field(default=None, max_length=500)


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    type: MovementType
    quantity: int
    previous_quantity: int
    new_quantity: int
    note: str | None
    created_by: int
    created_at: datetime


class DashboardRead(BaseModel):
    total_products: int
    total_units: int
    total_inventory_value: Decimal
    low_stock_products: int
    out_of_stock_products: int
    total_suppliers: int
    recent_movements: list[MovementRead]
