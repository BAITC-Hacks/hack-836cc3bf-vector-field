"""Python service boundary for the transport shapes in shared/contracts.ts.

Responses are the contract v1 dictionaries, not another Entity or snapshot model.
The live implementation should delegate to the same snapshot service as HTTP.
"""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolLimits:
    max_calls: int = 6
    timeout_seconds: int = 30
    list_limit_max: int = 200
    subgraph_hops_max: int = 2
    subgraph_limit_max: int = 200
    common_hops_max: int = 4
    common_limit_max: int = 50
    selected_gids_max: int = 20


LIMITS = ToolLimits()


class InvestigatorTools(Protocol):
    """Async, read-only adapter. Every response includes contract v1 `meta`."""

    async def get_entity_profile(self, gid: str) -> dict[str, Any]:
        """EntityResponse. gid must be an exact decimal string."""

    async def get_subgraph(
        self, gid: str, hops: int = 1, limit: int = 80
    ) -> dict[str, Any]:
        """SubgraphResponse. 1<=hops<=2; 1<=limit<=200."""

    async def rank_entities(
        self, role: str | None = None, cluster_id: int | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """EntityListResponse at offset=0. 1<=limit<=200."""

    async def find_common_recipients(
        self, request: dict[str, Any]
    ) -> dict[str, Any]:
        """CommonRecipientsResponse for contract v1 CommonRecipientsRequest."""


ROLES = frozenset(
    {"consolidator", "transit", "distributor", "terminal", "coordinator", "peripheral"}
)


def require_gid(gid: str) -> str:
    if not isinstance(gid, str) or not gid or not gid.isascii() or not gid.isdecimal():
        raise ValueError("gid must be a decimal string")
    return gid


def require_int(value: int, *, name: str, minimum: int, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum or 'unbounded'}]")
    return value
