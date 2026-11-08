"""EPUB reading order, navigation evidence, and section reconciliation."""

from pydantic import BaseModel, ConfigDict


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
