from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import analysis_finding  # noqa: E402,F401
from app.models import analysis_job  # noqa: E402,F401
from app.models import analysis_run  # noqa: E402,F401
from app.models import coverage_execution_config  # noqa: E402,F401
from app.models import github_app_installation  # noqa: E402,F401
from app.models import github_connection  # noqa: E402,F401
from app.models import installation_repository  # noqa: E402,F401
from app.models import oauth_state  # noqa: E402,F401
from app.models import quality_gate_config  # noqa: E402,F401
from app.models import repository  # noqa: E402,F401
from app.models import user  # noqa: E402,F401
from app.models import user_repository_access  # noqa: E402,F401
from app.models import user_session  # noqa: E402,F401
