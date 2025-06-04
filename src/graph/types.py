from dataclasses import dataclass


@dataclass
class TagResult:
    name: str
    classification_rationale: str
