# Store AI Review Snapshot On Analysis Run

Accepted on 2026-06-22. The LangChain review output will be stored as an `ai_review_json` JSONB snapshot on `analysis_runs`, rather than only as Markdown or as normalized tables. The review is historical evidence for one Analysis Run, and the MVP needs structured display data without introducing a query model for AI-generated content.

**Consequences**

`final_report_markdown` remains presentation output, while `ai_review_json` remains the structured source for summary, score, risk level, and suggestions. The schema can be promoted to normalized tables later if AI review content becomes a primary reporting dimension.
