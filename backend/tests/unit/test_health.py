"""Basic health check tests for Task API."""


def test_app_imports():
    """Verify core app modules can be imported."""
    from backend.app.models.task import Task, TaskCreate, TaskResponse
    assert Task is not None
    assert TaskCreate is not None
    assert TaskResponse is not None


def test_priority_enum_values():
    """Verify priority enum has expected values."""
    from backend.app.models.task import PriorityEnum
    assert PriorityEnum.low.value == "low"
    assert PriorityEnum.medium.value == "medium"
    assert PriorityEnum.high.value == "high"
    assert PriorityEnum.critical.value == "critical"


def test_status_enum_values():
    """Verify status enum has expected values."""
    from backend.app.models.task import StatusEnum
    assert StatusEnum.pending.value == "pending"
    assert StatusEnum.in_progress.value == "in_progress"
    assert StatusEnum.completed.value == "completed"
