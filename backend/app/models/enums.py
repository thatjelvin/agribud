from enum import Enum


class UserRole(str, Enum):
    """User roles per PRD §1.3 (Target Audience) and §5.3 (RBAC)."""

    farmer = "farmer"
    agribusiness = "agribusiness"
    financial_institution = "financial_institution"
    admin = "admin"


class RiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
