from pydantic import BaseModel, Field


class PreprocessingStatus(BaseModel):
    enabled: bool = Field(..., description="Whether SSS domain-specific preprocessing is enabled")
    bac_normalization: bool = Field(..., description="Column-wise Beam Angle Correction gain normalization active")
    stripe_noise_filter: bool = Field(..., description="2D-FFT horizontal stripe filter active")
    homomorphic_sharpening: bool = Field(..., description="Homomorphic edge sharpening active")
    shadow_inpainting: bool = Field(..., description="Acoustic shadow detection & inpainting active")
    shadow_threshold: float = Field(..., description="Acoustic shadow intensity threshold cutoff [0.0, 1.0]")
    shadow_inpaint_method: str = Field(..., description="Shadow inpainting algorithm ('telea' or 'ns')")
    target_size: list[int] = Field(..., description="YOLOv8 target input resolution [width, height]")


class HealthResponse(BaseModel):
    status: str
    model: dict | None = None
    database: dict | None = None
    model_loaded: bool | None = None
    preprocessing: PreprocessingStatus | dict | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: str | None = None


class ModelInfo(BaseModel):
    name: str
    version: str
    provider: str


class PredictionData(BaseModel):
    label: str
    confidence: float
    raw_scores: dict[str, float]


class PredictionResponse(BaseModel):
    success: bool = True
    prediction: PredictionData
    model: ModelInfo
    request_id: str
