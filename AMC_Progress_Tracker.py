# A program that tracks the user's progress in preparing for the AMC math competition on the 4th to 6th of August
import datetime
import json
import os
import matplotlib.pyplot as plt

SCORES_FILE = "amc_scores.json"
TARGET_SCORE = 100.0  # the score you're aiming to reach by competition day
TOTAL_QUESTIONS = 25  # the AMC has 25 questions, getting harder from #1 to #25
SOLID = 0.8  # accuracy at or above this means a section is "locked in"
WALL = 0.5   # accuracy below this marks where your wall begins

# The AMC groups its 25 questions into difficulty sections. Each (name, first, last).
SECTIONS = [
    ("Easy", 1, 10),
    ("Mid", 11, 20),
    ("Hard", 21, 25),
]

# Make a function to work out the date of the next AMC competition (4th August)
def next_competition_date():
    today = datetime.date.today()
    competition_date = datetime.date(today.year, 8, 4)
    if competition_date < today:
        competition_date = datetime.date(today.year + 1, 8, 4)
    return competition_date

# Make a function to print the date now and how many days until the competition
def print_date_and_countdown():
    today = datetime.date.today()
    competition_date = next_competition_date()
    days_until_competition = (competition_date - today).days
    print(f"Today's date: {today}")
    print(f"Days until AMC competition: {days_until_competition}")

# Load the full list of saved score records (each record is a dictionary)
def load_records():
    if not os.path.exists(SCORES_FILE):
        return []
    with open(SCORES_FILE, "r") as file:
        return json.load(file)

# Turn a string like "1, 2, 5, 8" into a clean, validated list of question numbers.
# Raises ValueError if anything isn't a whole number in range, so the caller can re-prompt.
def parse_question_numbers(raw, total=TOTAL_QUESTIONS):
    correct = set()
    for piece in raw.split(","):
        piece = piece.strip()
        if piece == "":
            continue  # allow blank entries / a fully blank line (= got none right)
        number = int(piece)  # raises ValueError on non-numbers
        if not 1 <= number <= total:
            raise ValueError(f"Question {number} is out of range 1-{total}")
        correct.add(number)
    return sorted(correct)

# Make a function to allow the user to input how many they answered and which they got right, then store it
def input_score_and_store():
    while True:
        try:
            answered = int(input(f"How many questions did you answer (attempt)? 0-{TOTAL_QUESTIONS}: "))
            if not 0 <= answered <= TOTAL_QUESTIONS:
                raise ValueError(f"You can only answer between 0 and {TOTAL_QUESTIONS} questions")
            raw = input(f"Enter the question numbers you got RIGHT (e.g. 1,2,3,7), 1-{TOTAL_QUESTIONS}: ")
            correct = parse_question_numbers(raw)
            if len(correct) > answered:
                raise ValueError(f"You marked {len(correct)} correct but only answered {answered}")

            percentage_score = (len(correct) / TOTAL_QUESTIONS) * 100
            wrong = answered - len(correct)
            print(f"You got {len(correct)}/{TOTAL_QUESTIONS} right = {percentage_score:.2f}%")
            # Remind the user to review the questions they got wrong
            if wrong > 0:
                print(f"⚠️  You answered {wrong} question(s) incorrectly - go back and check those before next time!")
            else:
                print("✅ Every question you answered was correct - nice work!")

            # Store each entry as a dictionary (with the per-question detail), save as JSON
            records = load_records()
            records.append({
                "date": str(datetime.date.today()),
                "score": round(percentage_score, 2),
                "answered": answered,
                "correct": correct,
            })
            with open(SCORES_FILE, "w") as file:
                json.dump(records, file, indent=2)
            break
        except ValueError as error:
            print(f"Invalid input ({error}). Please try again.")
            continue

# Read all stored scores back as parallel lists of dates and percentages
def read_scores():
    dates = []
    scores = []
    for record in load_records():
        dates.append(datetime.datetime.strptime(record["date"], "%Y-%m-%d").date())
        scores.append(float(record["score"]))
    return dates, scores

# Work out how fast you are improving, in percentage points gained per day.
# Uses a simple least-squares line of best fit through (day, score) points.
def calculate_growth_rate(dates, scores):
    n = len(scores)
    if n < 2:
        return 0.0  # need at least two scores to measure growth
    # Convert dates to "days since the first entry" so the maths is easy
    xs = [(d - dates[0]).days for d in dates]
    mean_x = sum(xs) / n
    mean_y = sum(scores) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, scores))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0  # all scores entered on the same day
    return numerator / denominator  # slope = % points per day

# Use the growth rate to predict your score on competition day
def project_competition_score(dates, scores):
    if not scores:
        return 0.0
    growth_per_day = calculate_growth_rate(dates, scores)
    days_left = (next_competition_date() - dates[-1]).days
    projected = scores[-1] + growth_per_day * days_left
    return max(0.0, min(100.0, projected))  # keep it within 0-100%

# Work out the weekly improvement you still need to hit your target by competition day.
# Returns % points per week required from your latest score.
def required_weekly_growth(dates, scores, target=TARGET_SCORE):
    if not scores:
        return 0.0
    gap = target - scores[-1]
    if gap <= 0:
        return 0.0  # already at or above the target
    days_left = (next_competition_date() - dates[-1]).days
    if days_left <= 0:
        return float("inf")  # competition is here and the target isn't met
    weeks_left = days_left / 7
    return gap / weeks_left

# Recommend which AMC problems to focus on based on your most recent score.
# The AMC has 25 questions that get harder from #1 to #25.
def recommend_difficulty(latest_score):
    if latest_score < 40:
        return "Foundations", "Drill problems 1-10 until they feel automatic."
    elif latest_score < 60:
        return "Intermediate", "Lock in problems 1-15 and start attempting 16-18."
    elif latest_score < 80:
        return "Advanced", "Push on problems 12-22; these decide qualification."
    else:
        return "Olympiad", "Attack problems 20-25 and begin AIME-level practice."

# ---- "Find Your Wall" diagnostic: which individual questions are you actually missing? ----

# For every question number, what fraction of your sessions did you get it right?
def accuracy_by_question(records, total=TOTAL_QUESTIONS):
    sessions = [r for r in records if "correct" in r]  # only sessions with per-question detail
    if not sessions:
        return {}
    accuracy = {}
    for question in range(1, total + 1):
        hits = sum(1 for r in sessions if question in r["correct"])
        accuracy[question] = hits / len(sessions)
    return accuracy

# Your "wall": the first question number where your accuracy drops below the WALL threshold.
# Everything before it is reliable; this is where your score starts leaking.
def find_the_wall(records, total=TOTAL_QUESTIONS):
    accuracy = accuracy_by_question(records, total)
    if not accuracy:
        return None
    for question in range(1, total + 1):
        if accuracy[question] < WALL:
            return question
    return total + 1  # no wall found - you're solid across the whole paper

# The questions worth drilling next: the lowest-numbered ones you haven't locked in yet.
# Early AMC questions are the easiest points to recover, so they give the biggest gain.
def recommend_focus_questions(records, n=3, total=TOTAL_QUESTIONS):
    accuracy = accuracy_by_question(records, total)
    if not accuracy:
        return []
    shaky = [q for q in range(1, total + 1) if accuracy[q] < SOLID]
    return shaky[:n]

# ---- Section diagnostic: how do you do across the Easy / Mid / Hard groups? ----

# For each AMC section, what fraction of its questions do you get right on average?
def accuracy_by_section(records):
    sessions = [r for r in records if "correct" in r]
    if not sessions:
        return {}
    section_accuracy = {}
    for name, first, last in SECTIONS:
        size = last - first + 1
        # total questions answered correctly in this section across every session
        hits = sum(sum(1 for q in r["correct"] if first <= q <= last) for r in sessions)
        section_accuracy[name] = hits / (len(sessions) * size)
    return section_accuracy

# Recommend the section to focus on next: the easiest one you haven't locked in yet,
# because lower-difficulty points are the cheapest to recover.
def recommend_focus_section(records):
    section_accuracy = accuracy_by_section(records)
    if not section_accuracy:
        return None
    for name, first, last in SECTIONS:  # SECTIONS is already easy -> hard
        if section_accuracy[name] < SOLID:
            return f"{name} (Q{first}-{last})"
    return None  # every section is locked in

# Split your misses into blanks (ran out of time) vs wrong answers (knowledge gaps).
# Returns the average number of each per session.
def pacing_insight(records):
    sessions = [r for r in records if "answered" in r and "correct" in r]
    if not sessions:
        return None
    avg_blank = sum(TOTAL_QUESTIONS - r["answered"] for r in sessions) / len(sessions)
    avg_wrong = sum(r["answered"] - len(r["correct"]) for r in sessions) / len(sessions)
    return avg_blank, avg_wrong

# Pull everything together: growth rate, projection, readiness and a difficulty rating
def analyze_progress():
    records = load_records()
    dates, scores = read_scores()
    if not scores:
        print("No scores recorded yet - enter a score to unlock your analysis.")
        return

    growth_per_day = calculate_growth_rate(dates, scores)
    growth_per_week = growth_per_day * 7
    latest = scores[-1]
    best = max(scores)
    projected = project_competition_score(dates, scores)
    level, advice = recommend_difficulty(latest)
    needed = required_weekly_growth(dates, scores)
    # On track if your current pace already meets the pace you need
    on_track = needed == 0.0 or growth_per_week >= needed

    print("\n===== AMC PROGRESS ANALYSIS =====")
    print(f"Latest score:        {latest:.1f}%")
    print(f"Personal best:       {best:.1f}%")
    print(f"Average score:       {sum(scores) / len(scores):.1f}%")
    trend = "improving" if growth_per_week > 0 else "slipping" if growth_per_week < 0 else "flat"
    print(f"Growth rate:         {growth_per_week:+.2f}% per week ({trend})")
    print(f"Projected on comp day: {projected:.1f}%")
    print(f"Target score:        {TARGET_SCORE:.1f}%")
    if needed == 0.0:
        print("Target status:       Already hitting your target - keep it up!")
    else:
        print(f"Needed growth:       {needed:+.2f}% per week to reach target")
        print(f"Target status:       {'ON TRACK' if on_track else 'BEHIND - increase your pace'}")
    print(f"Recommended level:   {level}")
    print(f"Coach's advice:      {advice}")

    # ---- The headline feature: how you score across the Easy / Mid / Hard sections ----
    section_accuracy = accuracy_by_section(records)
    if section_accuracy:
        print("\n----- SECTION BREAKDOWN -----")
        for name, first, last in SECTIONS:
            pct = section_accuracy[name] * 100
            mark = "locked in" if pct >= SOLID * 100 else "shaky" if pct >= WALL * 100 else "needs work"
            print(f"{name:<5} (Q{first}-{last}): {pct:5.0f}%  ({mark})")
        focus = recommend_focus_section(records)
        if focus:
            print(f"Focus section:      {focus}  (your biggest available gain)")
        else:
            print("Focus section:      none - every section is locked in. Aim higher!")

        # Split your misses into pacing (blanks) vs accuracy (wrong answers)
        pacing = pacing_insight(records)
        if pacing:
            avg_blank, avg_wrong = pacing
            if avg_blank >= 5:
                print(f"Pacing check:       you leave ~{avg_blank:.0f} questions BLANK per test - work on speed.")
            elif avg_wrong >= 5:
                print(f"Pacing check:       you ANSWER plenty but ~{avg_wrong:.0f} are wrong - work on accuracy.")
            else:
                print(f"Pacing check:       balanced (~{avg_blank:.0f} blank, ~{avg_wrong:.0f} wrong per test).")
    print("=================================\n")

# Make a function to read the scores from the file and print them out as a graph using matplotlib
def plot_scores():
    dates, scores = read_scores()
    plt.figure()  # start a fresh figure so this chart stands on its own
    plt.plot(dates, scores, marker='o', linestyle='-', color='blue', label='Your scores')
    # Show the exact value next to each dot (e.g. 100% or 99%)
    for date, score in zip(dates, scores):
        plt.annotate(f"{score:.0f}%", (date, score),
                     textcoords="offset points", xytext=(0, 8), ha='center')
    competition_date = next_competition_date()
    # Draw the projection: a dashed line from your latest score to where you're heading
    if len(scores) >= 2:
        projected = project_competition_score(dates, scores)
        plt.plot([dates[-1], competition_date], [scores[-1], projected],
                 linestyle=':', color='green', label=f'Projection ({projected:.0f}%)')
    plt.title("AMC Progress Tracker")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    # Show the x-axis from the first entry through to the next competition date
    plt.xlim(min(dates), competition_date)
    plt.ylim(0, 105)
    plt.axvline(competition_date, color='red', linestyle='--', label='AMC competition')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    plt.show()

# Draw a bar chart of your accuracy across the Easy / Mid / Hard sections.
# Green = locked in, yellow = shaky, red = needs work. This is the "look twice" view.
def plot_section_accuracy():
    records = load_records()
    section_accuracy = accuracy_by_section(records)
    if not section_accuracy:
        return  # no per-question data yet, nothing to draw
    plt.figure()  # start a fresh figure so this chart stands on its own
    labels = [f"{name}\n(Q{first}-{last})" for name, first, last in SECTIONS]
    percents = [section_accuracy[name] * 100 for name, _, _ in SECTIONS]
    colors = ['green' if p >= SOLID * 100 else 'orange' if p >= WALL * 100 else 'red'
              for p in percents]
    bars = plt.bar(labels, percents, color=colors)
    # Label each bar with its exact percentage
    for bar, p in zip(bars, percents):
        plt.annotate(f"{p:.0f}%", (bar.get_x() + bar.get_width() / 2, p),
                     textcoords="offset points", xytext=(0, 5), ha='center')
    plt.title("AMC Accuracy by Section")
    plt.xlabel("Section (easier <--> harder)")
    plt.ylabel("How often you get them right (%)")
    plt.ylim(0, 105)
    plt.tight_layout()
    plt.show()

# Main function to run the program
def main():
    print_date_and_countdown()
    while True:
        input_score_and_store()
        analyze_progress()
        plot_scores()
        plot_section_accuracy()
        continue_input = input("Do you want to enter another score? (y/n): ")
        if continue_input.lower() != 'y':
            break

if __name__ == "__main__":
    main()
