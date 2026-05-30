# A program that tracks the user's progress in preparing for the AMC math competition on the 4th to 6th of August
import datetime
import matplotlib.pyplot as plt

SCORES_FILE = "amc_scores.txt"
TARGET_SCORE = 100.0  # the score you're aiming to reach by competition day

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

# Make a function to allow the user to input their score as a fraction and turn it into a percentage and store in a file
def input_score_and_store():
    while True:
        score_fraction = input("Enter your score as a fraction (e.g. 15/25): ")
        try:
            numerator, denominator = map(int, score_fraction.split('/'))
            percentage_score = (numerator / denominator) * 100
            print(f"Your score as a percentage: {percentage_score:.2f}%")
            with open(SCORES_FILE, "a") as file:
                file.write(f"{datetime.date.today()}: {percentage_score:.2f}%\n")
                break
        except ValueError:
            print("Invalid input. Please enter the score in the format 'numerator/denominator")
            continue

# Read all stored scores back as parallel lists of dates and percentages
def read_scores():
    dates = []
    scores = []
    with open(SCORES_FILE, "r") as file:
        for line in file:
            date_str, score_str = line.strip().split(": ")
            dates.append(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
            scores.append(float(score_str.replace("%", "")))
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

# Pull everything together: growth rate, projection, readiness and a difficulty rating
def analyze_progress():
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
    print("=================================\n")

# Make a function to read the scores from the file and print them out as a graph using matplotlib
def plot_scores():
    dates, scores = read_scores()
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

# Main function to run the program
def main():
    print_date_and_countdown()
    while True:
        input_score_and_store()
        analyze_progress()
        plot_scores()
        continue_input = input("Do you want to enter another score? (y/n): ")
        if continue_input.lower() != 'y':
            break

if __name__ == "__main__":
    main()
