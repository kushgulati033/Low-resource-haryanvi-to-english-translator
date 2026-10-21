import csv
import re

input_file = "dataset.csv"
output_file = "bible_haryanvi_english_final.csv"

# Read CSV
with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

cleaned = []

for row in rows:

    text = row.get("Haryanvi", "")

    if not text:
        continue

    # Remove [L1], [L25], etc.
    text = re.sub(r'\[L\d+\]\s*', '', text)

    # Replace line breaks with spaces
    text = re.sub(r'\s*\n\s*', ' ', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove verse number ONLY from the beginning
    # Example: "25 यहूदा..." → "यहूदा..."
    text = re.sub(r'^\d+\s+', '', text)

    # Skip completely empty/punctuation-only rows
    if not text or re.fullmatch(r'[।\s]+', text):
        continue

    cleaned.append({
        "Haryanvi": text,
        "English Translation": ""
    })


# Write final CSV
with open(output_file, "w", encoding="utf-8-sig", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=["Haryanvi", "English Translation"]
    )

    writer.writeheader()
    writer.writerows(cleaned)


print("================================")
print("FINAL CLEANING COMPLETED")
print("================================")
print("Original rows:", len(rows))
print("Final rows:", len(cleaned))
print("Output:", output_file)