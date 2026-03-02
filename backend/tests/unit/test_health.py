"""Basic smoke tests for the Todo App backend."""


def test_python_version():
    """Verify Python version is 3.12+."""
    import sys
    assert sys.version_info >= (3, 12)


def test_dependencies_importable():
    """Verify core dependencies are installed."""
    import fastapi
    import sqlmodel
    import httpx
    assert fastapi is not None
    assert sqlmodel is not None
    assert httpx is not None


def test_sqlmodel_basics():
    """Verify SQLModel works for schema definition."""
    from sqlmodel import SQLModel, Field

    class SampleModel(SQLModel):
        name: str = Field(max_length=100)
        value: int = Field(default=0)

    item = SampleModel(name="test", value=42)
    assert item.name == "test"
    assert item.value == 42
