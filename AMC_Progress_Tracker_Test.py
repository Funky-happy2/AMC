import datetime
import json
import matplotlib
import AMC_Progress_Tracker as amc
from AMC_Progress_Tracker import (
    next_competition_date,
    print_date_and_countdown,
    input_score_and_store,
    load_records,
    read_scores,
    calculate_growth_rate,
    project_competition_score,
    required_weekly_growth,
    recommend_difficulty,
    analyze_progress,
    plot_scores,
)

matplotlib.use("Agg")  # use a non-popup backend so plot tests don't open a window


def write_scores(tmp_path, records):
    """Helper: write a list of score dictionaries to the JSON file."""
    (tmp_path / "amc_scores.json").write_text(json.dumps(records))


def test_next_competition_date():
    date = next_competition_date()
    assert date.month == 8
    assert date.day == 4
    assert date >= datetime.date.today()


def test_print_date_and_countdown(capsys):
    print_date_and_countdown()
    output = capsys.readouterr().out
    assert "Today's date" in output
    assert "Days until AMC competition" in output


def test_input_score_saves_dict_to_json(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "15/25")
    input_score_and_store()
    assert "60.00%" in capsys.readouterr().out

    # The file is valid JSON containing a list of dictionaries
    records = json.loads((tmp_path / "amc_scores.json").read_text())
    assert records == [{"date": str(datetime.date.today()), "score": 60.0}]


def test_input_score_appends_without_losing_old_records(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_scores(tmp_path, [{"date": "2026-01-01", "score": 40.0}])
    monkeypatch.setattr("builtins.input", lambda _: "20/40")
    input_score_and_store()

    records = json.loads((tmp_path / "amc_scores.json").read_text())
    assert len(records) == 2
    assert records[0] == {"date": "2026-01-01", "score": 40.0}
    assert records[1]["score"] == 50.0  # 20/40 = 50%


def test_input_score_rejects_bad_then_accepts_good(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    answers = iter(["not a fraction", "20/40"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    input_score_and_store()

    records = json.loads((tmp_path / "amc_scores.json").read_text())
    assert records[-1]["score"] == 50.0


def test_load_records_returns_empty_when_no_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert load_records() == []


def test_read_scores(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_scores(tmp_path, [
        {"date": "2026-01-01", "score": 80.0},
        {"date": "2026-02-01", "score": 90.0},
    ])
    dates, scores = read_scores()
    assert dates == [datetime.date(2026, 1, 1), datetime.date(2026, 2, 1)]
    assert scores == [80.0, 90.0]


def test_growth_rate_positive_when_improving():
    dates = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 11)]
    scores = [50.0, 70.0]  # +20% over 10 days = +2% per day
    assert calculate_growth_rate(dates, scores) == 2.0


def test_growth_rate_zero_with_single_score():
    assert calculate_growth_rate([datetime.date(2026, 1, 1)], [50.0]) == 0.0


def test_projection_extends_the_trend():
    dates = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 11)]
    scores = [50.0, 70.0]  # rising, so projection should beat the latest score
    assert project_competition_score(dates, scores) > 70.0


def test_projection_is_capped_at_100():
    dates = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 2)]
    scores = [90.0, 99.0]  # very steep rise would overshoot 100 without a cap
    assert project_competition_score(dates, scores) <= 100.0


def test_required_weekly_growth_is_zero_when_target_met():
    dates = [datetime.date(2026, 1, 1)]
    assert required_weekly_growth(dates, [100.0], target=100.0) == 0.0


def test_required_weekly_growth_positive_when_below_target():
    dates = [datetime.date.today()]
    # 30 points short, with weeks left, so a positive weekly pace is required
    assert required_weekly_growth(dates, [70.0], target=100.0) > 0.0


def test_recommend_difficulty_levels():
    assert recommend_difficulty(20)[0] == "Foundations"
    assert recommend_difficulty(50)[0] == "Intermediate"
    assert recommend_difficulty(70)[0] == "Advanced"
    assert recommend_difficulty(95)[0] == "Olympiad"


def test_analyze_progress_output(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    write_scores(tmp_path, [
        {"date": "2026-01-01", "score": 50.0},
        {"date": "2026-02-01", "score": 70.0},
    ])
    analyze_progress()
    output = capsys.readouterr().out
    assert "Growth rate" in output
    assert "Projected on comp day" in output
    assert "Target score" in output
    assert "Target status" in output
    assert "Recommended level" in output


def test_analyze_progress_handles_no_scores(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)  # no scores file at all
    analyze_progress()
    assert "No scores recorded yet" in capsys.readouterr().out


def test_plot_scores_runs(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_scores(tmp_path, [
        {"date": "2026-01-01", "score": 80.0},
        {"date": "2026-02-01", "score": 90.0},
    ])
    monkeypatch.setattr(amc.plt, "show", lambda: None)
    plot_scores()  # passes if it runs without raising
