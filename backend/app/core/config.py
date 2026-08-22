import os

class Settings:
    PROJECT_NAME: str = "Return-Risk Scorer API"
    ARTIFACTS_DIR: str = os.path.abspath("ml/artifacts")
    MODEL_PATH: str = os.path.join(ARTIFACTS_DIR, "model.json")
    EXPLAINER_PATH: str = os.path.join(ARTIFACTS_DIR, "explainer.pkl")
    THRESHOLD_CONFIG_PATH: str = os.path.join(ARTIFACTS_DIR, "threshold_config.json")
    FEATURE_MANIFEST_PATH: str = os.path.join(ARTIFACTS_DIR, "feature_manifest.json")
    EVAL_RESULTS_PATH: str = os.path.join(ARTIFACTS_DIR, "eval_results.json")
    DATABASE_URL: str = "sqlite:///./risk_manager.db"

settings = Settings()
