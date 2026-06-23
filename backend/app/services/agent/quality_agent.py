import json

from app.core.config import get_settings
from app.models.analysis_run import AnalysisRun
from app.services.agent.prompts import SYSTEM_PROMPT, build_ai_review_input
from app.services.agent.schemas import AIReviewError, AIReviewGenerated, AIReviewSkipped


def generate_ai_review_snapshot(*, analysis_run: AnalysisRun) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return AIReviewSkipped().model_dump(mode="json")

    try:
        from langchain_openai import ChatOpenAI

        review_input = build_ai_review_input(analysis_run)
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
        structured_llm = llm.with_structured_output(AIReviewGenerated)
        result = structured_llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    "Review this persisted quality gate evidence:\n"
                    f"{json.dumps(review_input, ensure_ascii=False, default=str)}",
                ),
            ]
        )
        if isinstance(result, AIReviewGenerated):
            snapshot = result
        else:
            snapshot = AIReviewGenerated.model_validate(result)
        data = snapshot.model_dump(mode="json")
        data["model"] = settings.openai_model
        return data
    except Exception:
        return AIReviewError().model_dump(mode="json")
