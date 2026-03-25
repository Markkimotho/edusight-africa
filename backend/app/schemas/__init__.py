from app.schemas.common import PaginatedResponse, ErrorDetail, ErrorResponse
from app.schemas.auth import TokenResponse, LoginRequest, RegisterRequest, RefreshRequest
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.schemas.student import StudentRead, StudentCreate, StudentUpdate, StudentDetail
from app.schemas.assessment import AssessmentRead, AssessmentCreate, AssessmentDetail
from app.schemas.prediction import PredictionRead
from app.schemas.observation import ObservationRead, ObservationCreate
from app.schemas.intervention import InterventionRead, InterventionCreate, InterventionUpdate

__all__ = [
    "PaginatedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "TokenResponse",
    "LoginRequest",
    "RegisterRequest",
    "RefreshRequest",
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "StudentRead",
    "StudentCreate",
    "StudentUpdate",
    "StudentDetail",
    "AssessmentRead",
    "AssessmentCreate",
    "AssessmentDetail",
    "PredictionRead",
    "ObservationRead",
    "ObservationCreate",
    "InterventionRead",
    "InterventionCreate",
    "InterventionUpdate",
]
