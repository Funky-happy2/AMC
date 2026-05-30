import datetime
import json
import matplotlib
matplotlib.use("Agg")  # non-popup backend so plot tests don't open a window
import pytest
import AMC_Progress_Tracker as amc

TODAY = datetime.date.today()


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    """Every test runs in a temp dir with the plot window stubbed out."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(amc.plt, "show", lambda: None)


def feed(monkeypatch, *values):
    """Feed a sequence of answers to successive input() prompts."""
    answers = iter(values)
    monkeypatch.setattr("builtins.input", lambda _: next(answers))


def save(records):
    with open("amc_scores.json", "w") as f:
        json.dump(records, f)


def saved():
    with open("amc_scores.json") as f:
        return json.load(f)


# ---- dates & countdown ----

def test_next_competition_date():
    date = amc.next_competition_date()
    assert (date.month, date.day) == (8, 4) and date >= TODAY


def test_print_date_and_countdown(capsys):
    amc.print_date_and_countdown()
    out = capsys.readouterr().out
    assert "Today's date" in out and "Days until AMC competition" in out


# ---- parsing & helpers ----

def test_parse_question_numbers():
    assert amc.parse_question_numbers("1, 2, 5, 8") == [1, 2, 5, 8]
    assert amc.parse_question_numbers("") == []        # blank = none right
    assert amc.parse_question_numbers("3,3,1") == [1, 3]  # dedupes and sorts


@pytest.mark.parametrize("bad", ["banana", "99"])  # non-number, out of range
def test_parse_question_numbers_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        amc.parse_question_numbers(bad)


def test_correct_count_handles_both_modes():
    assert amc.correct_count({"correct": [1, 2, 3]}) == 3  # detailed
    assert amc.correct_count({"num_correct": 4}) == 4       # quick
    assert amc.correct_count({"score": 50.0}) == 0          # missing


def test_load_records_returns_empty_when_no_file():
    assert amc.load_records() == []


def test_read_scores():
    save([{"date": "2026-01-01", "score": 80.0}, {"date": "2026-02-01", "score": 90.0}])
    dates, scores = amc.read_scores()
    assert dates == [datetime.date(2026, 1, 1), datetime.date(2026, 2, 1)]
    assert scores == [80.0, 90.0]


# ---- logging a session (both coach modes) ----

def test_detailed_mode_saves_question_list(monkeypatch, capsys):
    feed(monkeypatch, "1", "30", ",".join(str(q) for q in range(1, 19)))  # 18/30 = 60%
    amc.input_score_and_store()
    assert "60.00%" in capsys.readouterr().out
    r = saved()[0]
    assert (r["score"], r["answered"], r["correct"]) == (60.0, 30, list(range(1, 19)))


def test_quick_mode_saves_count_only(monkeypatch, capsys):
    feed(monkeypatch, "2", "20", "6")  # answered 20, 6 right = 20%
    amc.input_score_and_store()
    out = capsys.readouterr().out
    r = saved()[0]
    assert (r["score"], r["answered"], r["num_correct"]) == (20.0, 20, 6)
    assert "correct" not in r  # quick mode doesn't store which questions
    assert "Detailed mode is the better coach" in out  # nudges toward detailed


def test_mode_chooser_reprompts_on_bad_choice(monkeypatch):
    feed(monkeypatch, "9", "1", "3", "1,2,3")  # bad choice -> reprompt -> detailed
    amc.input_score_and_store()
    assert saved()[0]["correct"] == [1, 2, 3]


def test_reminds_to_check_wrong_answers(monkeypatch, capsys):
    feed(monkeypatch, "1", "5", "1,2,3")  # answered 5, 3 right -> 2 wrong
    amc.input_score_and_store()
    out = capsys.readouterr().out
    assert "2 question(s) incorrectly" in out and "check those" in out


def test_congratulates_when_all_answered_correct(monkeypatch, capsys):
    feed(monkeypatch, "1", "3", "1,2,3")
    amc.input_score_and_store()
    assert "Every question you answered was correct" in capsys.readouterr().out


def test_rejects_more_correct_than_answered(monkeypatch):
    feed(monkeypatch, "1", "2", "1,2,3,4,5", "5", "1,2,3,4,5")  # 5>2 retry, then valid
    amc.input_score_and_store()
    assert saved()[-1]["answered"] == 5


def test_appends_without_losing_old_records(monkeypatch):
    save([{"date": "2026-01-01", "score": 40.0, "correct": [1, 2]}])
    feed(monkeypatch, "1", "6", "1,2,3,4,5,6")
    amc.input_score_and_store()
    records = saved()
    assert len(records) == 2 and records[0]["correct"] == [1, 2] and records[1]["score"] == 20.0


def test_rejects_bad_then_accepts_good(monkeypatch):
    feed(monkeypatch, "1", "not a number", "6", "1,2,3,4,5,6")
    amc.input_score_and_store()
    assert saved()[-1]["score"] == 20.0


# ---- growth, projection, target ----

def test_growth_rate():
    d = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 11)]
    assert amc.calculate_growth_rate(d, [50.0, 70.0]) == 2.0          # +20% / 10 days
    assert amc.calculate_growth_rate([d[0]], [50.0]) == 0.0           # single score


def test_projection():
    rising = ([datetime.date(2026, 1, 1), datetime.date(2026, 1, 11)], [50.0, 70.0])
    steep = ([datetime.date(2026, 1, 1), datetime.date(2026, 1, 2)], [90.0, 99.0])
    assert amc.project_competition_score(*rising) > 70.0      # extends the trend
    assert amc.project_competition_score(*steep) <= 100.0     # capped at 100


def test_required_weekly_growth():
    assert amc.required_weekly_growth([datetime.date(2026, 1, 1)], [100.0], target=100.0) == 0.0
    assert amc.required_weekly_growth([TODAY], [70.0], target=100.0) > 0.0


@pytest.mark.parametrize("score,level", [
    (20, "Foundations"), (50, "Intermediate"), (70, "Advanced"), (95, "Olympiad")])
def test_recommend_difficulty(score, level):
    assert amc.recommend_difficulty(score)[0] == level


# ---- per-question & section diagnostics ----

def test_accuracy_by_question():
    records = [{"correct": [1, 2]}, {"correct": [1]}]
    acc = amc.accuracy_by_question(records, total=3)
    assert (acc[1], acc[2], acc[3]) == (1.0, 0.5, 0.0)
    assert amc.accuracy_by_question([{"score": 60.0}]) == {}  # ignores no-detail records


def test_find_the_wall():
    # q1,q2 = 100%, q3 = 50% (not below 0.5), q4 = 0% -> wall at q4
    records = [{"correct": [1, 2, 3]}, {"correct": [1, 2]}]
    assert amc.find_the_wall(records, total=5) == 4
    assert amc.find_the_wall([{"score": 50.0}]) is None  # no per-question data


def test_recommend_focus_questions():
    records = [{"correct": [1, 2]}]  # q1,q2 solid; q3+ missed
    assert amc.recommend_focus_questions(records, n=3, total=10) == [3, 4, 5]


def test_accuracy_by_section():
    records = [{"correct": list(range(1, 11)) + [11, 12, 13, 14, 15]}]  # all Easy, half Mid
    sec = amc.accuracy_by_section(records)
    assert (sec["Easy"], sec["Mid"], sec["Hard"]) == (1.0, 0.5, 0.0)
    assert amc.accuracy_by_section([{"score": 50.0}]) == {}


def test_recommend_focus_section():
    weak = [{"correct": list(range(1, 11)) + [11]}]  # Easy locked, Mid weak
    assert amc.recommend_focus_section(weak).startswith("Mid")
    assert amc.recommend_focus_section([{"correct": list(range(1, 31))}]) is None  # all solid


def test_pacing_insight():
    records = [{"answered": 20, "correct": [1, 2, 3, 4, 5]}]
    assert amc.pacing_insight(records) == (10, 15)  # 30-20 blank, 20-5 wrong
    assert amc.pacing_insight([{"score": 50.0}]) is None


# ---- the analysis dashboard ----

def test_analyze_progress_basic_output(capsys):
    save([{"date": "2026-01-01", "score": 50.0}, {"date": "2026-02-01", "score": 70.0}])
    amc.analyze_progress()
    out = capsys.readouterr().out
    for label in ("Growth rate", "Projected on comp day", "Target score",
                  "Target status", "Recommended level"):
        assert label in out


def test_analyze_progress_handles_no_scores(capsys):
    amc.analyze_progress()
    assert "No scores recorded yet" in capsys.readouterr().out


def test_analyze_progress_shows_section_breakdown(capsys):
    save([
        {"date": "2026-01-01", "score": 40.0, "answered": 12, "correct": list(range(1, 11))},
        {"date": "2026-02-01", "score": 48.0, "answered": 14, "correct": list(range(1, 13))},
    ])
    amc.analyze_progress()
    out = capsys.readouterr().out
    for label in ("SECTION BREAKDOWN", "Easy", "Mid", "Hard", "Focus section", "Pacing check"):
        assert label in out


# ---- charts just need to run without raising ----

def test_plot_section_accuracy_runs():
    save([{"date": "2026-01-01", "score": 40.0, "correct": [1, 2, 3, 11, 21]}])
    amc.plot_section_accuracy()


def test_plot_scores_runs():
    save([{"date": "2026-01-01", "score": 80.0}, {"date": "2026-02-01", "score": 90.0}])
    amc.plot_scores()
