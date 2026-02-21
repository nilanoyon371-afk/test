from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class MediaCategoryResponse(BaseModel):
    id: str
    title: str
    type: str
    icon: str
    color_hex: str
    playlist_url: str
    requires_pin: bool = False

class MediaProviderResponse(BaseModel):
    id: str
    name: str
    logo_url: Optional[str] = None
    is_active: bool
    categories: List[MediaCategoryResponse]

class MediaConfigData(BaseModel):
    title: str
    description: str
    providers: List[MediaProviderResponse]

class MediaConfigResponse(BaseModel):
    status: str = "success"
    data: MediaConfigData
