from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    password: bytes
    email: Optional[str] = None
    created: Optional[str] = None
    last_access: Optional[str] = None
    confirmed: Optional[str] = None
    author_name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
