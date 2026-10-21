import re
import csv

input_file = "bible.haryanvi.txt"
output_file = "dataset.csv"

# Read file
with open(input_file, "r", encoding="utf-8-sig") as f:
    text = f.read()

# Normalize line endings
text = text.replace("\r\n", "\n").replace("\r", "\n")

# Remove labels such as [L1], [L25], [L3000]
text = re.sub(r'\[L\d+\]\s*', '', text)

# Split into paragraphs using blank lines
paragraphs = re.split(r'\n\s*\n+', text)

cleaned_sentences = []

for paragraph in paragraphs:

    paragraph = paragraph.strip()

    if not paragraph:
        continue

    # Join wrapped lines inside the same paragraph
    paragraph = re.sub(r'\s*\n\s*', ' ', paragraph)

    # Split paragraph into sentences using danda
    sentences = re.split(r'(?<=।)\s*', paragraph)

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # Remove ONLY a verse number at the beginning
        # Example:
        # "25 यहूदा..." → "यहूदा..."
        #
        # Numbers later in the sentence are preserved.
        sentence = re.sub(r'^\d+\s+', '', sentence)

        # Normalize multiple spaces
        sentence = re.sub(r'\s+', ' ', sentence).strip()

        if sentence:
            cleaned_sentences.append(sentence)


# Create CSV
with open(output_file, "w", newline="", encoding="utf-8-sig") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Haryanvi",
        "English Translation"
    ])

    for sentence in cleaned_sentences:
        writer.writerow([
            sentence,
            ""
        ])


print("Cleaning completed!")
print("Translation units:", len(cleaned_sentences))
print("Output:", output_file)