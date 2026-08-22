from fastapi import APIRouter
from backend.app.models.schema import MetricsResponse
from backend.app.services.model_loader import model_loader

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    eval_res = model_loader.eval_results["cost_optimal"]
    thresh_conf = model_loader.threshold_config

    return MetricsResponse(
        precision=eval_res["precision"],
        recall=eval_res["recall"],
        f1=eval_res["f1"],
        roc_auc=eval_res["roc_auc"],
        chosen_threshold=thresh_conf["threshold"],
        fp_cost=thresh_conf["fp_cost"],
        fn_cost=thresh_conf["fn_cost"],
        total_cost_at_threshold=thresh_conf["total_cost_at_threshold"],
        cost_curve=thresh_conf["cost_curve"],
        eval_results=model_loader.eval_results,
        cost_sensitivity=model_loader.cost_sensitivity
    )
