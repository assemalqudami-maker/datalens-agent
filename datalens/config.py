import math
import os
from dataclasses import dataclass
from pathlib import Path

# Standard text rates per million tokens. Recheck when changing model or pricing.
# https://ai.google.dev/gemini-api/docs/pricing (checked 2026-11-03)
PRICES = {"gemini-3.5-flash-lite": (0.30, 2.50), "gemini-2.5-flash-lite": (0.10, 0.40)}


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("runtime")
    model: str = "gemini-3.5-flash-lite"
    max_turns: int = 10
    task_budget: float = 0.10
    daily_budget: float = 1.0
    max_output_tokens: int = 2048
    max_input_tokens: int = 24000
    timeout_seconds: int = 45

    def __post_init__(self):
        if self.model not in PRICES:
            raise ValueError("Unknown model pricing. Add verified rates before enabling this model.")
        if not 1 <= self.max_turns <= 20:
            raise ValueError("max_turns must be 1–20")
        if any(not math.isfinite(v) or v <= 0 for v in (self.task_budget, self.daily_budget)):
            raise ValueError("Budgets must be finite and positive")

    @classmethod
    def from_env(cls):
        return cls(
            data_dir=Path(os.getenv("DATALENS_DATA_DIR", "runtime")),
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            max_turns=int(os.getenv("DATALENS_MAX_TURNS", "10")),
            task_budget=float(os.getenv("DATALENS_TASK_BUDGET_USD", "0.10")),
            daily_budget=float(os.getenv("DATALENS_DAILY_BUDGET_USD", "1.00")),
        )

    def price(self, input_tokens: int, output_tokens: int) -> float:
        inp, out = PRICES[self.model]
        return (input_tokens * inp + output_tokens * out) / 1_000_000
