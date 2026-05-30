# AMC Progress Tracker

A Python coach that helps you prepare for the **AMC math competition** (held 4th–6th of August). Instead of just logging a score, you log **which questions you got right** — and the program finds your **wall**, the exact point where your paper starts leaking points, then tells you precisely what to drill next for the biggest gain.

## ⭐ The headline feature: "Find Your Wall"

The AMC's 25 questions get harder from #1 to #25. Everyone has a *wall* — the question number where they start falling apart. Your fastest score gains don't come from the hard problems you can't do; they come from the **easy-to-mid problems you're inconsistently missing.**

So the tracker:

- 🧱 **Finds your wall** — the first question where your accuracy drops below 50%.
- 🎯 **Names the exact questions to drill next** — your highest-value fixes (the lowest-numbered questions you haven't locked in).
- 📈 **Shows your realistic ceiling** — the score you'd reach by shoring those up.
- 🟢🟡🔴 **Charts accuracy per question** — green = locked in, yellow = shaky, red = past your wall.

```
----- FIND YOUR WALL -----
Your wall:           question #11 (accuracy drops off here)
Locked-in questions: 10/25
Drill these next:    #11, #12, #13  (your highest-value fixes)
Ceiling if you do:   52%  (up from 48%)
```

## What else it does

- 📅 **Counts down** the days until the next AMC competition.
- ✍️ **Records each session** — enter how many you answered and which you got right; it flags how many you got wrong and **reminds you to review them.** Saved as JSON with the date.
- 📈 **Calculates your growth rate** — percentage points improved per week (line of best fit through your history).
- 🔮 **Projects your competition-day score** based on your current trend.
- 🎯 **Tracks a target score** — tells you the weekly pace you need, and whether you're **ON TRACK** or **BEHIND**.
- 🧠 **Recommends a difficulty level** (Foundations → Intermediate → Advanced → Olympiad) with coaching advice.
- 📊 **Plots two graphs** — your score trend (with projection + competition date) and your per-question accuracy.

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
3. Enter **how many questions you answered** (attempted) this session.
4. Enter the question numbers you got right, e.g. `1,2,3,7,11`. It works out how many you got wrong and **reminds you to go back and check them.**
5. Read your analysis (growth rate, projection, target status, recommended level, **and your wall**) and view the two graphs.
6. Choose `y` to log another session, or `n` to quit.

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
| `amc_scores.json` | Auto-created when you log your first session. Stores your history as a JSON list of records, e.g. `{"date": "2026-05-30", "score": 60.0, "answered": 20, "correct": [1, 2, 3, 7]}`. Not committed to git — it's your personal data. |
| `.gitignore` | Tells git to ignore auto-generated Python folders (`__pycache__/`, `.pytest_cache/`) and your local score data. |
| `README.md` | This file. |

## Running the tests

The project comes with a full pytest suite. Run it with:

```bash
python3 -m pytest AMC_Progress_Tracker_Test.py -v
```

All tests should pass. They cover the date countdown, score input and validation, growth-rate maths, score projection (including the 0–100% cap), target-pace calculations, difficulty recommendations, and the graph — using fake input and a non-popup graph backend so nothing interrupts the run.
