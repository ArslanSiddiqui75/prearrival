"""Routing on the illustrative road graph. Pure functions, no network, no AI.

Roads are two-way. A route is {route: [node ids], legs: [{segment, name, from, to, minutes}], eta_min}.
"""

import heapq
import json
from pathlib import Path

# Heavy traffic multiplies a segment's normal travel time by this.
SLOW_FACTOR = 3
# For heavy traffic, offer an alternate only if it saves at least this many minutes.
MIN_SAVING_MIN = 2
NO_ROUTE = "No open route, contact dispatch"

MAP_PATH = Path(__file__).resolve().parent.parent / "fixtures/route/map.json"


def load_graph(path: Path = MAP_PATH) -> dict:
    return json.loads(Path(path).read_text())


def node(graph: dict, node_id: str) -> dict:
    return next(n for n in graph["nodes"] if n["id"] == node_id)


def segment(graph: dict, seg_id: str) -> dict:
    return next(s for s in graph["segments"] if s["id"] == seg_id)


def best_route(graph: dict, start: str, end: str, closed=frozenset(), slow=None) -> dict:
    """Fastest route by Dijkstra. closed = segment ids to skip; slow = {segment id: time multiplier}."""
    slow = slow or {}
    adj = {}
    for seg in graph["segments"]:
        if seg["id"] in closed:
            continue
        minutes = seg["minutes"] * slow.get(seg["id"], 1)
        adj.setdefault(seg["from"], []).append((seg["to"], seg, minutes))
        adj.setdefault(seg["to"], []).append((seg["from"], seg, minutes))

    dist, prev, heap = {start: 0.0}, {}, [(0.0, start)]
    while heap:
        d, here = heapq.heappop(heap)
        if here == end:
            break
        if d > dist[here]:
            continue
        for there, seg, minutes in adj.get(here, []):
            if d + minutes < dist.get(there, float("inf")):
                dist[there] = d + minutes
                prev[there] = (here, seg, minutes)
                heapq.heappush(heap, (dist[there], there))

    if end not in dist:
        return {"route": None, "legs": [], "eta_min": None}
    legs, here = [], end
    while here != start:
        before, seg, minutes = prev[here]
        legs.append({"segment": seg["id"], "name": seg["name"], "from": before, "to": here, "minutes": minutes})
        here = before
    legs.reverse()
    return {"route": [start] + [leg["to"] for leg in legs], "legs": legs, "eta_min": dist[end]}


def reroute(graph: dict, current_position: dict, end: str, incident: dict, current_route: dict, closed=frozenset(), slow=None) -> dict:
    """Decide whether to offer the crew an alternate after an incident on a segment ahead.

    current_position: {leg, node, remaining_min} from tracking.position_at (node = end of the current leg).
    incident: {segment, kind: "closed" | "slow"}.
    closed, slow: earlier incidents to keep avoiding.
    Returns {status: "offer" | "no_offer" | "no_route", alternate, eta_min, delta_min, kept_eta_min, saving_min, message}.
    """
    slow = dict(slow or {})
    closed = set(closed)
    at, remaining = current_position["node"], current_position["remaining_min"]
    ahead = current_route["legs"][current_position["leg"] + 1 :]
    planned_eta = remaining + sum(leg["minutes"] for leg in ahead)
    seg_id = incident["segment"]

    if incident["kind"] == "closed":
        closed.add(seg_id)
        alt = best_route(graph, at, end, closed=closed, slow=slow)
        if alt["route"] is None:
            return {"status": "no_route", "alternate": None, "eta_min": None, "delta_min": None,
                    "kept_eta_min": planned_eta, "saving_min": None, "message": NO_ROUTE}
        eta = remaining + alt["eta_min"]
        return {"status": "offer", "alternate": alt, "eta_min": eta, "delta_min": eta - planned_eta,
                "kept_eta_min": planned_eta, "saving_min": None, "message": ""}

    # Heavy traffic: the current route gets slower whether or not the crew changes route.
    slow[seg_id] = SLOW_FACTOR
    kept_eta = remaining + sum(leg["minutes"] * (SLOW_FACTOR if leg["segment"] == seg_id else 1) for leg in ahead)
    alt = best_route(graph, at, end, closed=closed, slow=slow)
    same_route = alt["route"] is None or [l["segment"] for l in alt["legs"]] == [l["segment"] for l in ahead]
    alt_eta = None if alt["route"] is None else remaining + alt["eta_min"]
    saving = None if alt_eta is None else kept_eta - alt_eta
    if same_route or saving < MIN_SAVING_MIN:
        return {"status": "no_offer", "alternate": None, "eta_min": kept_eta, "delta_min": kept_eta - planned_eta,
                "kept_eta_min": kept_eta, "saving_min": saving,
                "message": f"No alternate saves {MIN_SAVING_MIN}+ min"}
    return {"status": "offer", "alternate": alt, "eta_min": alt_eta, "delta_min": alt_eta - planned_eta,
            "kept_eta_min": kept_eta, "saving_min": saving, "message": ""}
