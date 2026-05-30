# AMC Progress Tracker

A small Python program that helps you prepare for the **AMC math competition** (held 4th–6th of August). You log your practice-test scores over time and the program tracks your progress, predicts how you'll do on competition day, and tells you what difficulty of problems to focus on next.

## What it does

- 📅 **Counts down** the days until the next AMC competition.
- ✍️ **Records your scores** — enter a score like `15/25` and it's saved (as a percentage with the date) to a local JSON file.
- 📈 **Calculates your growth rate** — how many percentage points you're improving per week (line of best fit through your history).
- 🔮 **Projects your competition-day score** based on your current trend.
- 🎯 **Tracks a target score** — tells you the weekly pace you need to hit your goal, and whether you're **ON TRACK** or **BEHIND**.
- 🧠 **Recommends a difficulty level** (Foundations → Intermediate → Advanced → Olympiad) with coaching advice on which AMC problems to drill.
- 📊 **Plots a graph** of your scores over time, with your projection and the competition date marked.

## Requirements

- Python 3
- [matplotlib](https://matplotlib.org/) (for the graph)

Install matplotlib if you don't have it:

```bash
pip install matplotlib
```

## How to use it

1. Run the program:

   ```bash
   python3 AMC_Progress_Tracker.py
   ```

2. It shows today's date and the days left until the competition.
3. Enter your latest practice score as a fraction, e.g. `18/25`.
4. Read your analysis (growth rate, projection, target status, recommended level) and view the graph.
5. Choose `y` to log another score, or `n` to quit.

Your scores are saved between runs, so the more you log, the more accurate your trend and projection become.

### Setting your target

Open `AMC_Progress_Tracker.py` and change this line near the top to whatever score you're aiming for:

```python
TARGET_SCORE = 100.0  # the score you're aiming to reach by competition day
```

## The files

| File | What it is |
|------|------------|
| `AMC_Progress_Tracker.py` | The main program. Contains all the logic: the countdown, score entry, growth-rate calculation, projection, target tracking, difficulty recommendation, and the graph. |
| `AMC_Progress_Tracker_Test.py` | The automated test suite (pytest). Tests every function so you can be confident the maths and file handling work correctly. |
| `amc_scores.json` | Auto-created when you log your first score. Stores your score history as a JSON list of records, e.g. `{"date": "2026-05-30", "score": 60.0}`. Not committed to git — it's your personal data. |
| `.gitignore` | Tells git to ignore auto-generated Python folders (`__pycache__/`, `.pytest_cache/`) and your local score data. |
| `README.md` | This file. |

## Running the tests

The project comes with a full pytest suite. Run it with:

```bash
python3 -m pytest AMC_Progress_Tracker_Test.py -v
```

All tests should pass. They cover the date countdown, score input and validation, growth-rate maths, score projection (including the 0–100% cap), target-pace calculations, difficulty recommendations, and the graph — using fake input and a non-popup graph backend so nothing interrupts the run.
