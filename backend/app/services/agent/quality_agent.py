from app.core.config import get_settings
from app.models.analysis_run import AnalysisRun
from app.services.agent.prompts import PROMPT_VERSION, build_ai_review_input
from app.services.agent.schemas import AIReviewError, AIReviewSkipped
from app.services.agent.tracing import build_invocation_config, configure_langsmith_from_settings


def generate_ai_review_snapshot(*, analysis_run: AnalysisRun) -> dict:
    settings = get_settings()
    configure_langsmith_from_settings(settings)
    if not settings.openai_api_key:
        return AIReviewSkipped().model_dump(mode="json")

    try:
        from app.services.agent.graph import compiled_review_graph

        evidence = build_ai_review_input(analysis_run)
        config = build_invocation_config(
            analysis_run=analysis_run,
            evidence=evidence,
            model=settings.openai_model,
            prompt_version=PROMPT_VERSION,
        )
        result = compiled_review_graph().invoke(
            {
                "analysis_run": analysis_run,
                "model": settings.openai_model,
                "prompt_version": PROMPT_VERSION,
            },
            config=config,
        )
        snapshot = result.get("final_snapshot")
        if isinstance(snapshot, dict) and snapshot.get("status") in {
            "generated",
            "skipped",
            "error",
        }:
            return snapshot
        return AIReviewError().model_dump(mode="json")
    except Exception:
        return AIReviewError().model_dump(mode="json")
