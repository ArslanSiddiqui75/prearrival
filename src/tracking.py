"""Simulated ambulance position on a route. Pure functions, no network, no AI.

Logistics only: nothing here reads or changes fields, NEWS2, priority or the prepare-for list.
"""

from src.route import SLOW_FACTOR, node

# 1 real second = SIM_SPEED simulated seconds.
SIM_SPEED = 10


def sim_elapsed_s(started_real: float, now_real: float) -> float:
    return max(0.0, now_real - started_real) * SIM_SPEED


def total_min(route: dict) -> float:
    return sum(leg["minutes"] for leg in route["legs"])


def position_at(route: dict, graph: dict, sim_elapsed: float) -> dict:
    """Where the ambulance is after sim_elapsed simulated seconds.

    Returns {lat, lon, segment, leg, node, remaining_min, eta_route_min, arrived}.
    node is the end of the current leg; remaining_min is the time left to reach it.
    """
    t = sim_elapsed / 60.0
    done = 0.0
    for i, leg in enumerate(route["legs"]):
        if t < done + leg["minutes"]:
            frac = (t - done) / leg["minutes"]
            a, b = node(graph, leg["from"]), node(graph, leg["to"])
            return {
                "lat": a["lat"] + (b["lat"] - a["lat"]) * frac,
                "lon": a["lon"] + (b["lon"] - a["lon"]) * frac,
                "segment": leg["segment"],
                "leg": i,
                "node": leg["to"],
                "remaining_min": done + leg["minutes"] - t,
                "eta_route_min": total_min(route) - t,
                "arrived": False,
            }
        done += leg["minutes"]
    end = node(graph, route["route"][-1])
    last = len(route["legs"]) - 1
    return {"lat": end["lat"], "lon": end["lon"], "segment": None, "leg": last, "node": end["id"],
            "remaining_min": 0.0, "eta_route_min": 0.0, "arrived": True}


def inject_roadblock(route: dict, position: dict, kind: str) -> dict | None:
    """Close or slow the next segment ahead. None when there is no segment ahead."""
    if position["arrived"] or position["leg"] + 1 >= len(route["legs"]):
        return None
    leg = route["legs"][position["leg"] + 1]
    return {"segment": leg["segment"], "name": leg["name"], "kind": kind}


def accept_alternate(route: dict, position: dict, alternate: dict) -> dict:
    """Crew accepted: keep the legs driven so far plus the current one, then follow the alternate."""
    legs = route["legs"][: position["leg"] + 1] + alternate["legs"]
    return {"route": [route["route"][0]] + [leg["to"] for leg in legs], "legs": legs, "eta_min": sum(l["minutes"] for l in legs)}


def keep_route(route: dict, incident: dict) -> dict:
    """Crew kept the route. Heavy traffic still slows that segment; a reported closure leaves timing as planned."""
    legs = [
        {**leg, "minutes": leg["minutes"] * SLOW_FACTOR} if incident["kind"] == "slow" and leg["segment"] == incident["segment"] else leg
        for leg in route["legs"]
    ]
    return {**route, "legs": legs, "eta_min": sum(l["minutes"] for l in legs)}


def halt_before(route: dict, position: dict) -> dict:
    """No open route: the ambulance stops at the end of its current leg."""
    legs = route["legs"][: position["leg"] + 1]
    return {"route": [route["route"][0]] + [leg["to"] for leg in legs], "legs": legs, "eta_min": None}


# ---------- simulation state (a plain dict kept in st.session_state by the board) ----------


def new_sim(graph: dict, fixture: str, run_id, now: float) -> dict:
    from src.route import best_route

    route = best_route(graph, graph["pickups"][fixture], graph["destination"])
    return {"run_id": run_id, "started": now, "route": route, "first_eta": route["eta_min"], "closed": [], "slow": {},
            "pending": None, "status": "", "rerouted_from": None, "halted": False}


def _hold_cap_s(sim: dict) -> float | None:
    """While an offer waits for the crew, the ambulance holds at the junction before the incident."""
    if not sim["pending"]:
        return None
    leg = sim["pending"]["leg"]
    return sum(l["minutes"] for l in sim["route"]["legs"][: leg + 1]) * 60


def sim_seconds(sim: dict, now: float) -> float:
    elapsed = sim_elapsed_s(sim["started"], now)
    cap = _hold_cap_s(sim)
    return elapsed if cap is None else min(elapsed, cap)


def sim_position(sim: dict, graph: dict, now: float) -> dict:
    return position_at(sim["route"], graph, sim_seconds(sim, now))


def _resume_from(sim: dict, now: float) -> float:
    """Restart the clock so the ambulance continues from where it held."""
    return now - sim_seconds(sim, now) / SIM_SPEED


def sim_inject(sim: dict, graph: dict, kind: str, now: float) -> dict:
    """Presenter injects a closure or heavy traffic on the next segment ahead."""
    from src.route import reroute

    sim = {**sim, "closed": list(sim["closed"]), "slow": dict(sim["slow"])}
    if sim["pending"] or sim["halted"]:
        return sim
    pos = sim_position(sim, graph, now)
    incident = inject_roadblock(sim["route"], pos, kind)
    if incident is None:
        sim["status"] = "No road segment ahead to block."
        return sim
    offer = reroute(graph, pos, graph["destination"], incident, sim["route"], closed=set(sim["closed"]), slow=sim["slow"])
    if kind == "closed":
        sim["closed"].append(incident["segment"])
    else:
        sim["slow"][incident["segment"]] = SLOW_FACTOR
    what = "Road closed" if kind == "closed" else "Heavy traffic"

    if offer["status"] == "offer":
        sim["pending"] = {"incident": incident, "offer": offer, "leg": pos["leg"]}
        if kind == "closed":
            sim["alert"] = f"Road closed ahead on {incident['name']}. Alternate route adds {offer['delta_min']:g} min."
        else:
            # The choice is between the slowed route and the alternate, so state the saving against staying.
            delay = offer["kept_eta_min"] - (offer["eta_min"] - offer["delta_min"])
            sim["alert"] = (f"Heavy traffic ahead on {incident['name']} (+{delay:g} min). "
                            f"Alternate route saves {offer['saving_min']:g} min.")
        sim["status"] = "Alternate offered, waiting for crew"
    elif offer["status"] == "no_offer":
        sim["route"] = keep_route(sim["route"], incident)
        sim["status"] = f"{what} on {incident['name']} adds {offer['delta_min']:g} min. {offer['message']}; route kept."
    else:
        sim["route"] = halt_before(sim["route"], pos)
        sim["halted"] = True
        sim["status"] = f"{what} on {incident['name']}. {offer['message']}. Arrival unknown."
    return sim


def sim_answer(sim: dict, graph: dict, accept: bool, now: float) -> dict:
    """The crew answers the alert. The route only changes on Accept."""
    if not sim["pending"]:
        return sim
    sim = dict(sim)
    pending = sim["pending"]
    # The offer was made from the end of this leg; the ambulance has held there since.
    pos = {"leg": pending["leg"]}
    before = total_min(sim["route"])
    started = _resume_from(sim, now)
    if accept:
        sim["route"] = accept_alternate(sim["route"], pos, pending["offer"]["alternate"])
        sim["rerouted_from"] = sim["rerouted_from"] if sim["rerouted_from"] is not None else before
        sim["status"] = f"ETA {sim['rerouted_from']:g} -> {total_min(sim['route']):g} min (rerouted)"
    else:
        sim["route"] = keep_route(sim["route"], pending["incident"])
        kept = "despite reported closure" if pending["incident"]["kind"] == "closed" else "through heavy traffic"
        sim["status"] = f"Crew kept route {kept} on {pending['incident']['name']}."
    sim["pending"] = None
    sim["alert"] = ""
    sim["started"] = started
    return sim
