import json
from pathlib import Path
from datetime import date

# --- CONFIG ---
today_str = date.today().strftime("%Y-%m-%d")

# Build the full path with the dynamic filename
# Build the full path with the dynamic filename
input_file = Path("rpscrape/racecards") / f"{today_str}.json"
output_dir = Path("output") / f"{today_str}"
output_dir.mkdir(parents=True, exist_ok=True)  # <-- Add parents=True

# --- LOAD DATA ---
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- FLATTEN & COLLECT RACES ---
races_by_course = {}

for country, courses in data.items():
    for course_name, race_times in courses.items():
        for off_time, race_data in race_times.items():
            if isinstance(race_data, dict) and "runners" in race_data:
                full_race = {
                    "country": country,
                    "course": course_name,
                    "off_time": off_time,
                    **race_data
                }
                # Group by course name (case-sensitive, but consistent in your data)
                if course_name not in races_by_course:
                    races_by_course[course_name] = []
                races_by_course[course_name].append(full_race)

# --- SAVE ONE FILE PER COURSE ---
for course, races in races_by_course.items():
    # Clean filename (in case of spaces/special chars – though unlikely)
    safe_name = "".join(c for c in course if c.isalnum() or c in (" ", "-", "_")).rstrip()
    output_file = output_dir / f"{safe_name}.json"
    with open(output_file, "w") as f:
        json.dump(races, f, indent=2)
    print(f"Saved {len(races)} race(s) for {course} to {output_file.name}")

print(f"\n✅ All done! Files saved to: {output_dir}")