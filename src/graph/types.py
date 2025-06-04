from dataclasses import dataclass
from typing import Optional

from src.models.tags import EntryCategory


@dataclass
class TagResult:
    name: str
    classification_rationale: str

    def to_entry_category(self, entry_id: int) -> EntryCategory:
        return EntryCategory(
            entry_id,
            category=self.name,
        )


@dataclass
class TaggerReviewResult:
    approved: bool
    reason: str
    comment: Optional[TagResult] = None
