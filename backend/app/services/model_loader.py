import os
import json
import pickle
from xgboost import XGBClassifier
from backend.app.core.config import settings

class ModelLoaderService:
    def __init__(self):
        self.model = None
        self.explainer = None
        self.threshold_config = None
        self.feature_manifest = None
        self.eval_results = None
        self.cost_sensitivity = None
        self.feature_cols = []
        self.threshold = 0.5

    def load(self):
        print("Loading ML artifacts into memory...")
        # Load feature manifest
        with open(settings.FEATURE_MANIFEST_PATH, "r") as f:
            self.feature_manifest = json.load(f)
        self.feature_cols = self.feature_manifest["features"]

        # Load XGBoost model
        self.model = XGBClassifier()
        self.model.load_model(settings.MODEL_PATH)

        # Load SHAP explainer
        with open(settings.EXPLAINER_PATH, "rb") as f:
            self.explainer = pickle.load(f)

        # Load threshold config
        with open(settings.THRESHOLD_CONFIG_PATH, "r") as f:
            self.threshold_config = json.load(f)
        self.threshold = self.threshold_config.get("threshold", 0.5)

        # Load evaluation results
        with open(settings.EVAL_RESULTS_PATH, "r") as f:
            self.eval_results = json.load(f)

        # Load cost sensitivity if available
        sens_path = os.path.join(settings.ARTIFACTS_DIR, "cost_sensitivity.json")
        if os.path.exists(sens_path):
            with open(sens_path, "r") as f:
                self.cost_sensitivity = json.load(f)

        print("ML artifacts successfully loaded!")

model_loader = ModelLoaderService()
