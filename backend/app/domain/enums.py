from enum import Enum


class UserRole(str, Enum):
    farmer = 'farmer'
    agribusiness = 'agribusiness'
    financial_institution = 'financial_institution'
    admin = 'admin'
