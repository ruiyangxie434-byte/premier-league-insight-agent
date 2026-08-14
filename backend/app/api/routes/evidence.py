from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.evidence import EvidenceCatalogData
from app.services.evidence_catalog import get_evidence_catalog

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get("", response_model=ApiResponse[EvidenceCatalogData], summary="获取数据证据目录")
async def evidence_catalog() -> ApiResponse[EvidenceCatalogData]:
    return ApiResponse(message="Evidence catalog loaded", data=get_evidence_catalog())

