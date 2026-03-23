from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    status: CheckStatus
    message: str
    fix_suggestion: str | None = None


class HealthCheck(ABC):
    """Base class for all health checks. Subclasses must set name and implement check()."""

    name: str = "Unnamed Check"

    @abstractmethod
    def check(self) -> CheckResult:
        pass

    def verbose_detail(self) -> str | None:
        """Override to return inline detail text for --verbose mode."""
        return None


class HealthCheckSuite:
    """Registry and runner for health checks."""

    def __init__(self) -> None:
        self._checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        self._checks.append(check)

    def run_all(self) -> list[tuple[HealthCheck, CheckResult]]:
        return [(c, c.check()) for c in self._checks]

    def has_errors(self) -> bool:
        """Run all checks and return True if any returned ERROR."""
        results = self.run_all()
        return any(r.status == CheckStatus.ERROR for _, r in results)
