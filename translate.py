import os
import json
import pandas as pd
import tempfile

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# CONFIGURATION
# ============================================================

START_ROW = 4726
END_ROW = 4825

INPUT_FILE = "C:/Desktop/capstone/bible_haryanvi_english_final.csv"
OUTPUT_FILE = INPUT_FILE

MODEL = "gemini-3.1-flash-lite"


# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)


# ============================================================
# TRANSLATION INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are a professional Haryanvi to English translator.

Translate each Haryanvi sentence into accurate, natural English.

Rules:
1. Preserve the exact meaning.
2. Do not add or remove information.
3. Do not summarize or explain.
4. Preserve names, places, numbers and tense.
5. Return exactly one English translation per sentence.
6. Return only the requested JSON array.
"""


# ============================================================
# TRANSLATE BATCH
# ============================================================

def translate_batch(sentences):

    input_data = [
        {"id": int(row_id), "Haryanvi": sentence}
        for row_id, sentence in sentences
    ]

    prompt = f"""
Translate these Haryanvi sentences into English.

Return only a JSON array in this format:

[
    {{"id": 720, "english": "English translation"}}
]

Requirements:
- Return every ID exactly once.
- Do not omit or add IDs.
- Do not combine sentences.
- Return only valid JSON.

Sentences:
{json.dumps(input_data, ensure_ascii=False)}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json"
        )
    )

    result = json.loads(response.text)

    if not isinstance(result, list):
        raise ValueError("Gemini did not return a JSON array.")

    expected_ids = {row_id for row_id, _ in sentences}
    received_ids = [
        item.get("id") for item in result
    ]

    if len(received_ids) != len(expected_ids):
        raise ValueError("Translation count does not match input count.")

    if set(received_ids) != expected_ids:
        raise ValueError("Missing or unexpected translation IDs.")

    if len(set(received_ids)) != len(received_ids):
        raise ValueError("Gemini returned duplicate IDs.")

    translations = {}

    for item in result:
        translation = item.get("english")

        if not isinstance(translation, str) or not translation.strip():
            raise ValueError(
                f"Empty or invalid translation for ID {item['id']}"
            )

        translations[item["id"]] = translation.strip()

    return translations


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("Loading dataset...")

    df = pd.read_csv(INPUT_FILE, dtype=str, keep_default_na=False)

    if len(df.columns) == 0:
        raise ValueError("The CSV file has no columns.")

    print(f"Total rows: {len(df)}")

    # --------------------------------------------------------
    # IDENTIFY THE HARYANVI COLUMN
    # --------------------------------------------------------

    if "Haryanvi" in df.columns:
        haryanvi_col = "Haryanvi"
    elif "text" in df.columns:
        haryanvi_col = "text"
    else:
        haryanvi_col = df.columns[0]

    # --------------------------------------------------------
    # IDENTIFY OR CREATE THE ENGLISH COLUMN
    # --------------------------------------------------------

    if "English" in df.columns:
        english_col = "English"
    elif "english" in df.columns:
        english_col = "english"
    elif len(df.columns) >= 2:
        english_col = df.columns[1]
    else:
        english_col = "English"
        df[english_col] = ""

    # Keep exactly two columns in the required order.
    df = df[[haryanvi_col, english_col]].copy()

    df.columns = ["Haryanvi", "English"]

    # --------------------------------------------------------
    # VALIDATE ROW RANGE (1-BASED)
    # --------------------------------------------------------

    if START_ROW < 1 or END_ROW < START_ROW:
        raise ValueError("Invalid START_ROW or END_ROW.")

    if END_ROW > len(df):
        raise ValueError(
            f"END_ROW {END_ROW} exceeds dataset size {len(df)}."
        )

    # --------------------------------------------------------
    # SELECT ROWS
    # --------------------------------------------------------

    start_idx = START_ROW - 1
    end_idx = END_ROW

    print(f"Translating rows {START_ROW} to {END_ROW}...")

    # --------------------------------------------------------
    # PREPARE SENTENCES
    # --------------------------------------------------------

    sentences = []

    for idx in range(start_idx, end_idx):

        sentence = df.at[idx, "Haryanvi"].strip()

        if not sentence:
            print(f"Skipping empty Haryanvi row {idx + 1}.")
            continue

        sentences.append((idx + 1, sentence))

    if not sentences:
        print("No sentences available to translate.")
        return

    print(f"Sentences to translate: {len(sentences)}")

    # --------------------------------------------------------
    # TRANSLATE
    # --------------------------------------------------------

    translations = translate_batch(sentences)

    # --------------------------------------------------------
    # WRITE TRANSLATIONS INTO COLUMN 2
    # --------------------------------------------------------

    for row_id, translation in translations.items():

        idx = row_id - 1

        # Preserve the original Haryanvi sentence.
        # Update only the English translation.
        df.at[idx, "English"] = translation

    # --------------------------------------------------------
    # SAVE TO THE SAME CSV FILE
    # --------------------------------------------------------

    output_dir = os.path.dirname(os.path.abspath(OUTPUT_FILE))

    fd, temp_path = tempfile.mkstemp(
        suffix=".csv",
        dir=output_dir
    )

    os.close(fd)

    try:
        df.to_csv(
            temp_path,
            index=False,
            encoding="utf-8-sig"
        )

        # Replace the original only after the new CSV is saved.
        os.replace(temp_path, OUTPUT_FILE)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # --------------------------------------------------------
    # COMPLETED
    # --------------------------------------------------------

    print("\n========================================")
    print("TRANSLATION COMPLETED SUCCESSFULLY")
    print("========================================")
    print(f"Rows translated: {START_ROW} to {END_ROW}")
    print(f"Translations written: {len(translations)}")
    print(f"Total rows preserved: {len(df)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Column 1: Haryanvi")
    print("Column 2: English")


if __name__ == "__main__":
    main()
