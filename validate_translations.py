"""
Haryanvi -> English Dataset Validation Tool
Checks CSV structure and flags suspicious rows for manual review.
The original dataset is never modified.

Run:
    python validate_translations.py
or:
    python validate_translations.py "C:/path/to/dataset.csv"
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_INPUT = Path(r"C:/Desktop/capstone/bible_haryanvi_english_final.csv")
SOURCE_CANDIDATES = ("Haryanvi", "Source")
TARGET_CANDIDATES = ("English Translation", "English", "Translation", "Target")
MIN_ENGLISH_WORDS = 2
MAX_LENGTH_RATIO = 8.0
MIN_LENGTH_RATIO = 0.08


def find_column(fieldnames, candidates):
    lookup = {name.strip().casefold(): name for name in fieldnames if name}
    for candidate in candidates:
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]
    return None


def words(text):
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def main():
    input_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_INPUT
    if not input_path.exists():
        print(f"ERROR: CSV not found: {input_path}")
        print('Usage: python validate_translations.py "C:/path/to/dataset.csv"')
        sys.exit(1)

    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row.")
            source_col = find_column(reader.fieldnames, SOURCE_CANDIDATES)
            target_col = find_column(reader.fieldnames, TARGET_CANDIDATES)
            if not source_col or not target_col:
                raise ValueError(
                    f"Could not identify columns. Found: {reader.fieldnames}. "
                    "Expected Haryanvi and English/English Translation."
                )
            rows = []
            for line_num, raw in enumerate(reader, start=2):
                rows.append({
                    "line": line_num,
                    "source": (raw.get(source_col) or "").strip(),
                    "target": (raw.get(target_col) or "").strip(),
                })
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    source_counts = Counter(r["source"].casefold() for r in rows if r["source"])
    target_counts = Counter(
        re.sub(r"\s+", " ", r["target"].casefold()) for r in rows if r["target"]
    )
    flagged = []
    flag_counts = Counter()

    for row in rows:
        src, tgt = row["source"], row["target"]
        flags = []
        if not src:
            flags.append("MISSING_HARYANVI")
        if not tgt:
            flags.append("MISSING_ENGLISH")
        else:
            if src and src.casefold() == tgt.casefold():
                flags.append("SOURCE_EQUALS_TRANSLATION")
            if words(tgt) < MIN_ENGLISH_WORDS:
                flags.append("ENGLISH_TOO_SHORT")
            if re.search(r"[।॥]", tgt):
                flags.append("POSSIBLE_HARYANVI_PUNCTUATION_IN_ENGLISH")
            if re.search(r"\b(?:TODO|TRANSLATE|N/?A|NULL|NONE)\b", tgt, re.I):
                flags.append("PLACEHOLDER_TEXT")
            if any(mark in tgt for mark in ("|", "```", "<escape>", "[L")):
                flags.append("POSSIBLE_MARKDOWN_OR_SOURCE_ARTIFACT")
            if "\t" in tgt or "\n" in tgt or "\r" in tgt:
                flags.append("EMBEDDED_LINE_BREAK_OR_TAB")
            if re.search(r"\b([\w’'-]+)(?:\s+\1){2,}\b", tgt, re.I):
                flags.append("REPEATED_WORD_PATTERN")

        if src:
            if source_counts[src.casefold()] > 1:
                flags.append("DUPLICATE_HARYANVI_SOURCE")
            if tgt:
                source_words = max(words(src), 1)
                target_words = max(words(tgt), 1)
                ratio = target_words / source_words
                if ratio > MAX_LENGTH_RATIO:
                    flags.append("ENGLISH_MUCH_LONGER_THAN_SOURCE")
                elif ratio < MIN_LENGTH_RATIO and source_words >= 5:
                    flags.append("ENGLISH_MUCH_SHORTER_THAN_SOURCE")

        normalized_target = re.sub(r"\s+", " ", tgt.casefold())
        if normalized_target and target_counts[normalized_target] > 1:
            flags.append("DUPLICATE_ENGLISH_TRANSLATION")

        flags = list(dict.fromkeys(flags))
        for flag in flags:
            flag_counts[flag] += 1
        if flags:
            flagged.append((row, flags))

    report_path = input_path.with_name("validation_report.csv")
    summary_path = input_path.with_name("validation_summary.txt")
    with report_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "CSV Line", "Haryanvi", "English Translation",
            "Validation Flags", "Manual Review Needed"
        ])
        for row, flags in flagged:
            writer.writerow([row["line"], row["source"], row["target"], "; ".join(flags), "YES"])

    clean_count = len(rows) - len(flagged)
    summary = [
        "Haryanvi -> English Dataset Validation Summary",
        "=" * 48,
        f"Input file: {input_path}",
        f"Detected source column: {source_col}",
        f"Detected English column: {target_col}",
        f"Total data rows: {len(rows)}",
        f"Rows with no automatic flags: {clean_count}",
        f"Rows flagged for review: {len(flagged)}",
        "",
        "Flag counts (one row can have multiple flags):",
    ]
    summary.extend([f"  {name}: {count}" for name, count in sorted(flag_counts.items())]
                   or ["  No structural or heuristic flags found."])
    summary += [
        "",
        "Important:",
        "- These checks find missing values, duplicates, and unusual patterns.",
        "- No flags does NOT guarantee that a translation is accurate.",
        "- Manually review flagged rows for meaning, names, verse numbers, and context.",
        "- The original CSV is not modified.",
        f"- Detailed report: {report_path}",
    ]
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    print(f"\nDetailed report saved to: {report_path}")
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
