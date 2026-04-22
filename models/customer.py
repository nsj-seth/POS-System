from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    id:             int
    name:           str
    phone:          Optional[str]
    email:          Optional[str]
    total_purchases: int   = 0
    total_spent:    float  = 0.0
    created_at:     str    = ""