"""Deterministic Evidence facts from trusted tool outputs, using contract v1.

The common-recipient tool returns paths but no Evidence array. These facts are
derived from its verified response so findings can cite paths without asking a
model to invent IDs, counts, or the meaning of a graph path.
"""

import hashlib
import json
from typing import Any, Mapping

from .boundary import require_gid


def _path_id(kind: str, snapshot_id: str, gid: str, payload: object) -> str:
    encoded = json.dumps(
        [snapshot_id, kind, gid, payload], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"{kind}:{gid}:{digest}:v1"


def common_recipient_evidence(response: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return path/source facts, rejecting malformed common-recipient results.

    This checks the response's own structural consistency. The live service
    remains responsible for checking that every path edge exists in snapshot.
    """
    try:
        meta = response["meta"]
        snapshot_id = meta["snapshot_id"]
        selected = response["selected_gids"]
        max_hops = response["max_hops"]
        mode = response["mode"]
        items = response["items"]
        limitations = response["limitations"]
        total = response["total"]
        truncated = response["truncated"]
    except (KeyError, TypeError) as error:
        raise ValueError("malformed CommonRecipientsResponse") from error
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("missing snapshot_id")
    if not isinstance(selected, list) or not 1 <= len(selected) <= 20:
        raise ValueError("selected_gids must contain 1..20 gids")
    for gid in selected:
        require_gid(gid)
    if len(set(selected)) != len(selected):
        raise ValueError("selected_gids must be unique")
    if type(max_hops) is not int or not 1 <= max_hops <= 4:
        raise ValueError("max_hops must be 1..4")
    if mode != ("direct" if max_hops == 1 else "reachable"):
        raise ValueError("common-recipient mode disagrees with max_hops")
    if not isinstance(items, list) or type(total) is not int or total < len(items):
        raise ValueError("invalid common-recipient items/total")
    if type(truncated) is not bool or truncated != (total > len(items)):
        raise ValueError("invalid common-recipient truncated flag")
    if (
        not isinstance(limitations, list)
        or any(not isinstance(code, str) for code in limitations)
        or "path_not_money_provenance" not in limitations
    ):
        raise ValueError("common-recipient path limitation is required")

    facts: list[dict[str, Any]] = []
    seen_recipients: set[str] = set()
    seen_ids: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("invalid common-recipient item")
        recipient = require_gid(item.get("gid"))
        if recipient in seen_recipients or recipient in selected:
            raise ValueError("duplicate or selected gid as common recipient")
        seen_recipients.add(recipient)
        paths = item.get("paths")
        if not isinstance(paths, list) or len(paths) != len(selected):
            raise ValueError("one witness path per source is required")
        by_source: dict[str, list[str]] = {}
        for path in paths:
            if not isinstance(path, Mapping):
                raise ValueError("invalid witness path")
            source = require_gid(path.get("source_gid"))
            gids = path.get("gids")
            if source not in selected or source in by_source or not isinstance(gids, list):
                raise ValueError("invalid path source")
            for gid in gids:
                require_gid(gid)
            if (
                not 2 <= len(gids) <= max_hops + 1
                or gids[0] != source
                or gids[-1] != recipient
                or len(set(gids)) != len(gids)
            ):
                raise ValueError("invalid directed witness path")
            by_source[source] = gids
        if set(by_source) != set(selected):
            raise ValueError("witness paths do not cover all selected gids")

        source_list = ";".join(selected)
        recipient_fact = {
            "evidence_id": _path_id("common", snapshot_id, recipient, [selected, by_source]),
            "gid": recipient,
            "metric": "common_recipient_sources",
            "value": source_list,
            "unit": "text",
            "rule_id": "common_recipients_v1",
            "source": "derived",
            "scope": "observed_intrabank_july_2026",
            "text": f"Узел {recipient} структурно достижим от выбранных gid: {source_list}.",
            "limitations": list(dict.fromkeys([*limitations, "date_only"])),
        }
        facts.append(recipient_fact)
        for source in selected:
            gids = by_source[source]
            fact = {
                "evidence_id": _path_id("path", snapshot_id, source, gids),
                "gid": source,
                "metric": "common_recipient_path",
                "value": "→".join(gids),
                "unit": "text",
                "rule_id": "common_recipients_v1",
                "source": "derived",
                "scope": "observed_intrabank_july_2026",
                "text": f"Наблюдаемый направленный путь: {' → '.join(gids)}.",
                "limitations": list(dict.fromkeys([*limitations, "date_only"])),
            }
            facts.append(fact)
    for fact in facts:
        if fact["evidence_id"] in seen_ids:
            raise ValueError("duplicate derived evidence_id")
        seen_ids.add(fact["evidence_id"])
    return facts
