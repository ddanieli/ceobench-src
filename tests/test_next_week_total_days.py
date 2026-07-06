import json
import urllib.request
from types import SimpleNamespace
from typing import Any, cast

from saas_bench.api_server import NovaMindAPIServer
from saas_bench.completion import is_weekly_simulation_complete


class FakeTools:
    def __init__(self, current_day: int, total_days: int):
        self.current_day = current_day
        self.config = SimpleNamespace(total_days=total_days)

    def set_current_day(self, day: int):
        self.current_day = day


class FakeSimulator:
    def __init__(self, next_day: int):
        self.next_day = next_day
        self.step_week_calls = 0

    def step_week(self):
        self.step_week_calls += 1
        return SimpleNamespace(day=self.next_day)


def make_server(
    current_day: int,
    total_days: int,
    next_day: int,
) -> tuple[NovaMindAPIServer, FakeSimulator, FakeTools]:
    tools = FakeTools(current_day=current_day, total_days=total_days)
    simulator = FakeSimulator(next_day=next_day)
    return NovaMindAPIServer(tools=cast(Any, tools), simulator=simulator), simulator, tools


def post_next_week(server: NovaMindAPIServer) -> dict[str, Any]:
    prediction = {"point": 1.0, "lower": 0.0, "upper": 2.0}
    body = json.dumps({
        "rationale": "test terminal boundary",
        "predictions": {
            "cash_1wk": prediction,
            "cash_4wk": prediction,
            "cash_12wk": prediction,
            "cash_26wk": prediction,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{server.port}/next-week",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_game_status(server: NovaMindAPIServer) -> dict[str, Any]:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{server.port}/game-status"
    ) as resp:
        return json.loads(resp.read())



def test_weekly_completion_predicate_handles_non_multiple_day_limits():
    assert not is_weekly_simulation_complete(day=42, total_days=50)
    assert is_weekly_simulation_complete(day=49, total_days=50)
    assert not is_weekly_simulation_complete(day=7, total_days=14)
    assert is_weekly_simulation_complete(day=14, total_days=14)

def test_next_week_does_not_advance_when_week_would_exceed_total_days():
    server, simulator, tools = make_server(current_day=49, total_days=50, next_day=56)

    result = server.advance_week(rationale="already near the limit")

    assert result["success"] is True
    assert result["completed"] is True
    assert result["terminal"] is True
    assert result["day"] == 49
    assert result["total_days"] == 50
    assert "exceed total_days=50" in result["message"]
    assert result["dashboard"].startswith("=== Week 7 Dashboard (Day 49) ===")
    assert "Simulation complete at day 49" in result["dashboard"]
    assert simulator.step_week_calls == 0
    assert tools.current_day == 49


def test_next_week_advances_when_full_week_fits_and_marks_terminal_afterward():
    server, simulator, tools = make_server(current_day=42, total_days=50, next_day=49)

    result = server.advance_week(rationale="last full week")

    assert result["success"] is True
    assert result["day"] == 49
    assert result["total_days"] == 50
    assert result["completed"] is True
    assert result["terminal"] is True
    assert "exceed total_days=50" in result["message"]
    assert result["dashboard"].startswith("=== Week 7 Dashboard (Day 49) ===")
    assert "Simulation complete at day 49" in result["dashboard"]
    assert simulator.step_week_calls == 1
    assert tools.current_day == 49


def test_next_week_reports_not_completed_when_more_full_weeks_fit():
    server, simulator, tools = make_server(current_day=0, total_days=14, next_day=7)

    result = server.advance_week(rationale="first week")

    assert result["success"] is True
    assert result["day"] == 7
    assert result["total_days"] == 14
    assert result["completed"] is False
    assert result["terminal"] is False
    assert "message" not in result
    assert "Simulation Complete" not in result["dashboard"]
    assert simulator.step_week_calls == 1
    assert tools.current_day == 7


def test_next_week_http_contract_reports_completed_without_advancing():
    server, simulator, tools = make_server(current_day=49, total_days=50, next_day=56)
    server.start()
    try:
        result = post_next_week(server)
        status = get_game_status(server)
    finally:
        server.stop()

    assert result["success"] is True
    assert result["completed"] is True
    assert result["terminal"] is True
    assert result["day"] == 49
    assert result["dashboard"].startswith("=== Week 7 Dashboard (Day 49) ===")
    assert status["day"] == 49
    assert status["total_days"] == 50
    assert status["completed"] is True
    assert simulator.step_week_calls == 0
    assert tools.current_day == 49
