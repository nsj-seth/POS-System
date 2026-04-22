from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    id:            int
    name:          str
    category_id:   Optional[int]
    category_name: Optional[str]
    price:         float
    quantity:      int
    barcode:       Optional[str]
    low_stock_qty: int