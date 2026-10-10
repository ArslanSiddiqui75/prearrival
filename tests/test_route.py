"""Simulated tracking and rerouting. Logistics only: never touches fields, NEWS2, priority or prepare-for."""

import copy

from src.decide import decide
from src.news import score_news
from src.route import MIN_SAVING_MIN, NO_ROUTE, SLOW_FACTOR, best_route, load_graph, reroute
from src.tracking import SIM_SPEED, accept_alternate, inject_roadblock, keep_route, position_at, sim_elapsed_s

GRAPH = load_graph()
END = GRAPH["destination"]


def _route(fx):
    return best_route(GRAPH, GRAPH["pickups"][fx], END)


def _tiny(alt_minutes):
    """start -a(2)- mid -b(2)- end, plus a detour mid -c(alt)- end."""
    return {
        "nodes": [{"id": i, "name": i, "lat": 0.0, "lon": float(n)} for n, i in enumerate(["start", "mid", "end"])],
        "segments": [
            {"id": "a", "from": "start", "to": "mid", "name": "A road", "minutes": 2},
            {"id": "b", "from": "mid", "to": "end", "name": "B road", "minutes": 2},
            {"id": "c", "from": "mid", "to": "end", "name": "C detour", "minutes": alt_minutes},
        ],
    }


def test_map_is_marked_illustrative():
    assert GRAPH["illustrative"] is True
    assert 15 <= len(GRAPH["segments"]) <= 25


def test_fastest_path_matches_the_spoken_etas():
    assert _route("a")["eta_min"] == 8
    assert _route("a")["route"] == ["i8", "zp", "g8", "pims"]
    assert _route("b")["eta_min"] == 12


def test_closed_segment_ahead_offers_the_fastest_open_route():
    route = _route("a")
    pos = position_at(route, GRAPH, 0)
    incident = inject_roadblock(route, pos, "closed")
    assert incident["segment"] == route["legs"][1]["segment"]
    offer = reroute(GRAPH, pos, END, incident, route)
    assert offer["status"] == "offer"
    assert incident["segment"] not in [leg["segment"] for leg in offer["alternate"]["legs"]]
    assert offer["eta_min"] == 11 and offer["delta_min"] == 3


def test_slow_segment_with_alternate_saving_less_than_threshold_is_not_offered():
    g = _tiny(alt_minutes=2 * SLOW_FACTOR - (MIN_SAVING_MIN - 1))  # saves 1 min
    route = best_route(g, "start", "end")
    pos = position_at(route, g, 0)
    offer = reroute(g, pos, "end", inject_roadblock(route, pos, "slow"), route)
    assert offer["status"] == "no_offer"
    assert offer["eta_min"] == 2 + 2 * SLOW_FACTOR


def test_slow_segment_with_alternate_saving_threshold_or_more_is_offered():
    g = _tiny(alt_minutes=2 * SLOW_FACTOR - MIN_SAVING_MIN)  # saves exactly 2 min
    route = best_route(g, "start", "end")
    pos = position_at(route, g, 0)
    offer = reroute(g, pos, "end", inject_roadblock(route, pos, "slow"), route)
    assert offer["status"] == "offer"
    assert offer["saving_min"] == MIN_SAVING_MIN
    assert [leg["segment"] for leg in offer["alternate"]["legs"]] == ["c"]


def test_no_open_route():
    g = _tiny(alt_minutes=3)
    g["segments"] = [s for s in g["segments"] if s["id"] != "c"]
    route = best_route(g, "start", "end")
    pos = position_at(route, g, 0)
    offer = reroute(g, pos, "end", inject_roadblock(route, pos, "closed"), route)
    assert offer["status"] == "no_route"
    assert offer["message"] == NO_ROUTE
    assert offer["eta_min"] is None


def test_nothing_ahead_on_the_last_segment():
    route = _route("a")
    pos = position_at(route, GRAPH, (route["eta_min"] - 1) * 60)
    assert inject_roadblock(route, pos, "closed") is None


def test_position_moves_along_the_route_and_eta_decreases():
    route = _route("b")
    p0, p1, p2 = (position_at(route, GRAPH, s) for s in (0, 90, 400))
    assert (p0["lat"], p0["lon"]) != (p1["lat"], p1["lon"]) != (p2["lat"], p2["lon"])
    assert p0["eta_route_min"] == 12
    assert p0["eta_route_min"] > p1["eta_route_min"] > p2["eta_route_min"]
    assert p2["leg"] > p0["leg"]
    done = position_at(route, GRAPH, 13 * 60)
    assert done["arrived"] and done["eta_route_min"] == 0


def test_sim_clock_runs_at_sim_speed():
    assert sim_elapsed_s(100.0, 106.0) == 6 * SIM_SPEED


def test_accept_keeps_position_and_follows_the_alternate():
    route = _route("a")
    pos = position_at(route, GRAPH, 60)
    offer = reroute(GRAPH, pos, END, inject_roadblock(route, pos, "closed"), route)
    new = accept_alternate(route, pos, offer["alternate"])
    after = position_at(new, GRAPH, 60)
    assert (after["lat"], after["lon"]) == (pos["lat"], pos["lon"])
    assert new["eta_min"] == 11


def test_keep_route_in_traffic_slows_that_segment_only():
    route = _route("a")
    pos = position_at(route, GRAPH, 0)
    incident = inject_roadblock(route, pos, "slow")
    kept = keep_route(route, incident)
    assert kept["eta_min"] == route["eta_min"] + route["legs"][1]["minutes"] * (SLOW_FACTOR - 1)


def test_tracking_never_changes_priority_or_prepare_for():
    fields = {"hr": 105, "sbp": 120, "dbp": 80, "spo2": 96, "rr": None, "temp_c": None,
              "consciousness": "not_alert", "on_oxygen": False, "mechanism": "head_injury", "eta_min": 8}
    snapshot = copy.deepcopy(fields)
    before = decide(fields, score_news(fields))

    route = _route("a")
    pos = position_at(route, GRAPH, 30)
    offer = reroute(GRAPH, pos, END, inject_roadblock(route, pos, "closed"), route)
    accept_alternate(route, pos, offer["alternate"])

    assert fields == snapshot
    assert decide(fields, score_news(fields)) == before
    assert before["priority"] == "P1" and before["prepare_for"] == ["resus bay", "CT", "senior review"]


def test_route_changes_only_after_the_crew_accepts():
    from src.tracking import new_sim, sim_answer, sim_inject, sim_position, total_min

    sim = new_sim(GRAPH, "a", 1, now=0.0)
    offered = sim_inject(sim, GRAPH, "closed", now=1.0)
    assert offered["pending"] and offered["route"] == sim["route"]
    # While unanswered, the ambulance holds at the junction before the closure.
    held = sim_position(offered, GRAPH, 500.0)
    assert held["eta_route_min"] == 5

    kept = sim_answer(offered, GRAPH, False, now=500.0)
    assert kept["route"] == sim["route"] and not kept["pending"]

    accepted = sim_answer(offered, GRAPH, True, now=500.0)
    assert total_min(accepted["route"]) == 11
    assert accepted["status"] == "ETA 8 -> 11 min (rerouted)"
    assert sim_position(accepted, GRAPH, 500.0)["lat"] == held["lat"]
