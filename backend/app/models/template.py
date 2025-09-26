from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import SQLModel, Field, JSON, Column
from sqlalchemy import Text, DateTime


class TemplateAsset(SQLModel):
    """Asset reference in template"""
    key: str
    type: str  # 'static' | 'cid'


class Template(SQLModel, table=True):
    """Template model for email templates"""
    __tablename__ = "templates"
    __table_args__ = {'extend_existing': True}
    
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    subject_template: str = Field(sa_column=Column(Text))
    body_template: str = Field(sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    required_vars: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    assets: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
