"""
cache_utils.py
──────────────
Thin helpers around Django's cache framework (backed by Redis).
All cache keys are namespaced so they're easy to inspect and invalidate.

Usage:
    from core.cache_utils import get_overview_cache, set_overview_cache, invalidate_user_cache
"""

from django.core.cache import cache

# ─── TTLs ────────────────────────────────────────────────────────────────────
OVERVIEW_TTL        = 60 * 2       # 2 minutes  — dashboard data, slightly stale is fine
SAVINGS_GOALS_TTL   = 60 * 5       # 5 minutes  — goals don't change that often
BENEFICIARIES_TTL   = 60 * 10      # 10 minutes — rarely changes


# ─── Key builders ────────────────────────────────────────────────────────────
def _overview_key(user_id: int) -> str:
    return f"wallet:overview:{user_id}"

def _savings_goals_key(user_id: int) -> str:
    return f"wallet:savings_goals:{user_id}"

def _beneficiaries_key(user_id: int) -> str:
    return f"wallet:beneficiaries:{user_id}"


# ─── Overview ────────────────────────────────────────────────────────────────
def get_overview_cache(user_id: int):
    """Return cached overview data or None."""
    return cache.get(_overview_key(user_id))

def set_overview_cache(user_id: int, data: dict) -> None:
    cache.set(_overview_key(user_id), data, timeout=OVERVIEW_TTL)


# ─── Savings goals ───────────────────────────────────────────────────────────
def get_savings_goals_cache(user_id: int):
    return cache.get(_savings_goals_key(user_id))

def set_savings_goals_cache(user_id: int, data: list) -> None:
    cache.set(_savings_goals_key(user_id), data, timeout=SAVINGS_GOALS_TTL)


# ─── Beneficiaries ───────────────────────────────────────────────────────────
def get_beneficiaries_cache(user_id: int):
    return cache.get(_beneficiaries_key(user_id))

def set_beneficiaries_cache(user_id: int, data: list) -> None:
    cache.set(_beneficiaries_key(user_id), data, timeout=BENEFICIARIES_TTL)


# ─── Invalidation ────────────────────────────────────────────────────────────
def invalidate_user_cache(user_id: int) -> None:
    """
    Call this whenever a user's wallet/goals/beneficiaries change
    (after deposit, transfer, savings op, etc.) so stale data is never served.
    """
    cache.delete_many([
        _overview_key(user_id),
        _savings_goals_key(user_id),
        _beneficiaries_key(user_id),
    ])