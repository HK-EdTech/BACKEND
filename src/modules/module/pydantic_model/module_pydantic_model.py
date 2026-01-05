from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ModuleWithPermissions(BaseModel):
    """Single module with aggregated permissions"""
    module_code: str
    module_eng_name: str
    module_chi_name: str
    seq_no: int
    route: str
    description: Optional[str] = None
    descriptive_message: Optional[str] = None
    parent_module_code: Optional[str] = None
    permissions: List[str]  # Aggregated permissions: ["read", "write", "create", "delete"]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileWithModulesResponse(BaseModel):
    """Extended profile response with optional modules"""
    profile: dict  # Use existing ProfileResponse type
    modules: Optional[List[ModuleWithPermissions]] = None

    class Config:
        from_attributes = True
