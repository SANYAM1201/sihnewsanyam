from app.config import Settings, get_settings
from app.preprocessing.identity_preprocessor import IdentityPreprocessor
from app.services.inference_service import InferenceService
from app.services.mock_model_service import MockModelService


def create_inference_service(settings: Settings | None = None) -> InferenceService:
    """Build an ``InferenceService`` based on the configured provider.

    Supported providers
    -------------------
    * ``mock`` — deterministic placeholder (no real ML).
    * ``sonar`` — Colab-trained YOLOv8s marine-debris detector.

    Raises
    ------
    ValueError
        If ``MODEL_PROVIDER`` is not a recognised provider name.
    """
    if settings is None:
        settings = get_settings()

    if settings.sss_enable_processing:
        from app.preprocessing.sonar_preprocessor import SonarPreprocessor
        from app.preprocessing.yolo_preprocessor import YOLOPreprocessingConfig

        yolo_config = YOLOPreprocessingConfig(
            target_size=settings.yolo_target_size,
            normalize=settings.yolo_normalize,
        )
        preprocessor = SonarPreprocessor(
            apply_sss_processing=settings.sss_enable_processing,
            apply_bac=settings.sss_enable_bac,
            apply_stripe_filter=settings.sss_enable_stripe_filter,
            apply_sharpening=settings.sss_enable_sharpening,
            apply_shadow_inpainting=settings.sss_enable_shadow_inpainting,
            shadow_threshold=settings.sss_shadow_threshold,
            shadow_inpaint_method=settings.sss_shadow_inpaint_method,
            yolo_config=yolo_config,
        )
    else:
        preprocessor = IdentityPreprocessor()

    if settings.model_provider == "mock":
        model = MockModelService()
    elif settings.model_provider == "sonar":
        from app.services.sonar_model_service import SonarModelService

        model = SonarModelService(model_path=settings.model_path)
    else:
        raise ValueError(
            f"Unsupported MODEL_PROVIDER: {settings.model_provider!r}. "
            "Supported providers: mock, sonar"
        )

    service = InferenceService(preprocessor=preprocessor, model=model)
    service.load()
    return service
