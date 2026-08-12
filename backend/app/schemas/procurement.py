from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.procurement import ItemCategory, QuotationStatus


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_person: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    is_active: bool


class RequestItemCreate(BaseModel):
    category: ItemCategory
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit: str | None = Field(default=None, max_length=30)


class QuotationRequestCreate(BaseModel):
    request_date: date | None = None
    required_date: date | None = None
    scope_description: str | None = Field(default=None, max_length=1000)
    items: list[RequestItemCreate] = []


class QuotationItemCreate(BaseModel):
    category: ItemCategory
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit: str | None = Field(default=None, max_length=30)
    rate: float = Field(ge=0)
    tax: float = Field(default=0, ge=0, le=100)


class QuotationCreate(BaseModel):
    vendor_id: int
    quotation_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)
    items: list[QuotationItemCreate] = []


class QuotationItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ItemCategory
    description: str
    quantity: float
    unit: str | None = None
    rate: float
    amount: float
    tax: float
    final_amount: float


class QuotationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor: VendorRead
    quotation_date: date | None = None
    total_amount: float
    status: QuotationStatus
    remarks: str | None = None
    items: list[QuotationItemRead] = []


class RequestItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ItemCategory
    description: str
    quantity: float
    unit: str | None = None


class QuotationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    request_date: date | None = None
    required_date: date | None = None
    scope_description: str | None = None
    status: str
    selected_vendor_id: int | None = None
    created_by: int | None = None
    created_at: datetime
    items: list[RequestItemRead] = []
    quotations: list[QuotationRead] = []


class VendorComparisonRow(BaseModel):
    quotation_id: int
    vendor: VendorRead
    total_amount: float
    rank: int = 0
    status: str


class VendorComparison(BaseModel):
    request_id: int
    rows: list[VendorComparisonRow]
    lowest_amount: float | None = None
    highest_amount: float | None = None
    difference: float | None = None
    average_amount: float | None = None
    savings_from_l1: float | None = None
    selected_vendor_id: int | None = None


class SelectVendorRequest(BaseModel):
    vendor_id: int
    comments: str | None = None