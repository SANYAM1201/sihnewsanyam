from __future__ import annotations

from app.preprocessing.base import Preprocessor
from app.schemas.ml import ModelMetadata, PredictionResult, PreprocessedInput
from app.services.model_service import ModelService


class InferenceService:
    """Orchestrates preprocessing and model inference.

    The API layer calls ``predict(raw_bytes)`` without knowing the details
    of either preprocessing or model execution.
    """

    def __init__(self, preprocessor: Preprocessor, model: ModelService) -> None:
        self._preprocessor = preprocessor
        self._model = model

    def load(self) -> None:
        """Load the underlying model."""
        self._model.load()

    @property
    def is_model_loaded(self) -> bool:
        return self._model.is_loaded

    def predict(self, raw_image_bytes: bytes) -> PredictionResult:
        import time

        t0 = time.perf_counter()
        preprocessed: PreprocessedInput = self._preprocessor.process(raw_image_bytes)
        t_prep = time.perf_counter() - t0
        try:
            from app.monitoring.metrics import PREPROCESSING_TIME

            PREPROCESSING_TIME.observe(t_prep)
        except Exception:
            pass

        t1 = time.perf_counter()
        result = self._model.predict(preprocessed)
        t_infer = time.perf_counter() - t1
        try:
            from app.monitoring.metrics import INFERENCE_TIME

            INFERENCE_TIME.observe(t_infer)
        except Exception:
            pass

        return result

    def metadata(self) -> ModelMetadata:
        return self._model.metadata()
