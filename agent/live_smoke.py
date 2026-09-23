"""Real-provider smoke through the existing API and calculated snapshot.

Run after pipeline and with OPENAI_API_KEY set. The script never prints secrets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.service import SnapshotService
from pipeline.run import DEFAULT_OUT

from .openai_model import model_from_environment


def main() -> int:
    parser = argparse.ArgumentParser(description="Live Investigator provider smoke")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_OUT / "snapshot.json")
    parser.add_argument("--scenario", choices=("ranking", "node", "all"), default="ranking")
    args = parser.parse_args()

    model = model_from_environment()
    if model is None:
        print("BLOCKED: set OPENAI_API_KEY and install backend/requirements.txt")
        return 2
    if not args.snapshot.is_file():
        print("BLOCKED: snapshot missing; run python -m pipeline first")
        return 2
    service = SnapshotService.from_file(args.snapshot)
    client = TestClient(create_app(service=service, model=model,
                                   static_dir=Path("no-frontend-build")))
    gid = service.summary()["top_nodes"][0]["gid"]
    questions = {
        "ranking": "Какие узлы наиболее приоритетны для дальнейшей проверки и почему?",
        "node": f"Что известно об узле {gid} и какие признаки поддерживают его приоритет?",
    }
    scenarios = ("ranking", "node") if args.scenario == "all" else (args.scenario,)
    print(f"provider=OpenAI model={model.model} snapshot_id={service.meta['snapshot_id']}")
    for scenario in scenarios:
        response = client.post("/api/investigate", json={
            "question": questions[scenario], "selected_gids": [gid],
            "snapshot_id": service.meta["snapshot_id"],
        })
        if response.status_code != 200:
            print(f"{scenario}: FAIL HTTP {response.status_code}")
            return 1
        answer = response.json()
        calls = answer["tool_calls"]
        print(f"{scenario}: status={answer['status']} tools={[call['name'] for call in calls]} "
              f"findings={len(answer['findings'])} evidence={len(answer['evidence'])}")
        if (
            answer["status"] != "completed" or not calls or not answer["findings"]
            or not answer["evidence"] or answer["meta"] != service.meta
            or any(call["status"] != "completed" for call in calls)
        ):
            print(f"{scenario}: FAIL {answer['message']}")
            return 1
        for fact in answer["evidence"]:
            profile = service.profiles.get(fact["gid"])
            if profile is None or fact not in profile["evidence"]:
                print(f"{scenario}: FAIL evidence differs from snapshot")
                return 1
        if client.get(f"/api/entities/{gid}").status_code != 200:
            print(f"{scenario}: FAIL core profile route")
            return 1
    print("PASS: live model, real tools, verified snapshot evidence, existing API")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
