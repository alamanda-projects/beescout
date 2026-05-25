# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/domains.py
# # # Function: BaseModel Data Domain - standardised team domains
# # # =======================

from pydantic import BaseModel
from typing import Optional


# Domain baru. `name` di-slugify server-side jadi kunci matching lowercase,
# `label` adalah nama tampil di UI.
class DomainCreate(BaseModel):
    name: str
    label: str
    description: Optional[str] = ""


# Update domain — semua field opsional (partial update / PATCH).
# `name` tidak bisa diubah: itu kunci akses kontrak yang dipakai user existing.
# `is_default` sengaja tidak diekspos: domain default di-seed otomatis oleh
# /setup (#74), bukan dipromosikan via API.
class DomainUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
