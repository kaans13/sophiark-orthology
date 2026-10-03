
from pathlib import Path
import csv
import gzip
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orthology"

FILES = [
    "go-basic.obo",
    "HUMAN-uniprot.gaf.gz",
    "MOUSE-uniprot.gaf.gz",
    "human_genes.tsv",
    "mouse_genes.tsv",
    "human_to_mouse.tsv",
    "mouse_to_human.tsv",
    "manifest.json",
]

errors = []
warnings = []


def error(message):
    errors.append(message)
    print(f"  [ERROR] {message}")


def warn(message):
    warnings.append(message)
    print(f"  [WARN]  {message}")


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def read_tsv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        yield from csv.reader(f, delimiter="\t")


def check_obo():
    section("1. GO ONTOLOGY")
    path = RAW / "go-basic.obo"
    terms = set()
    obsolete = set()
    in_term = False
    current_id = None

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if line == "[Term]":
                    in_term = True
                    current_id = None
                elif line.startswith("["):
                    in_term = False
                elif in_term and line.startswith("id: "):
                    current_id = line[4:].strip()
                    if current_id in terms:
                        error(f"Duplicate GO ID: {current_id}")
                    terms.add(current_id)
                elif in_term and line == "is_obsolete: true":
                    if current_id:
                        obsolete.add(current_id)

        print(f"  GO terms: {len(terms):,}")
        print(f"  Obsolete terms: {len(obsolete):,}")

        if not terms:
            error("No GO terms found.")
        else:
            print("  [OK] OBO parsed successfully.")

        return terms, obsolete

    except Exception as exc:
        error(f"OBO reading failed: {exc}")
        return set(), set()


def check_gaf(filename, go_terms, obsolete):
    section(f"GAF: {filename}")
    path = RAW / filename

    rows = 0
    malformed = 0
    invalid_go = 0
    obsolete_go = 0
    empty_go = 0
    evidence = {}
    namespaces = {}
    seen = set()
    duplicates = 0
    first_record = None

    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="strict") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip() or line.startswith("!"):
                    continue

                fields = line.rstrip("\r\n").split("\t")
                rows += 1

                if len(fields) != 17:
                    malformed += 1
                    if malformed <= 5:
                        warn(
                            f"{filename}:{line_number}: "
                            f"{len(fields)} columns (expected 17)"
                        )
                    continue

                if first_record is None:
                    first_record = fields

                go_id = fields[4]
                evidence_code = fields[6]

                if not go_id:
                    empty_go += 1
                elif go_id not in go_terms:
                    invalid_go += 1
                elif go_id in obsolete:
                    obsolete_go += 1

                evidence[evidence_code] = evidence.get(evidence_code, 0) + 1

                # A GAF annotation is identified by its database,
                # object ID, qualifier, GO ID, reference and evidence.
                key = (
                    fields[0], fields[1], fields[3],
                    fields[4], fields[5], fields[6]
                )
                if key in seen:
                    duplicates += 1
                else:
                    seen.add(key)

        print(f"  Total data rows: {rows:,}")
        print(f"  Malformed rows: {malformed:,}")
        print(f"  Invalid GO IDs: {invalid_go:,}")
        print(f"  Obsolete GO IDs: {obsolete_go:,}")
        print(f"  Empty GO IDs: {empty_go:,}")
        print(f"  Duplicate annotation keys: {duplicates:,}")

        if first_record:
            print(f"  First record: {first_record[0]} / "
                  f"{first_record[1]} / {first_record[4]}")

        if malformed:
            error(f"{filename}: malformed rows found.")
        if invalid_go:
            error(f"{filename}: GO IDs absent from the OBO file.")
        if empty_go:
            error(f"{filename}: annotations with empty GO IDs.")
        if obsolete_go:
            warn(f"{filename}: obsolete GO annotations found.")
        if duplicates:
            warn(f"{filename}: duplicate annotation keys found.")

        print("  Most common evidence codes:")
        for code, count in sorted(
            evidence.items(), key=lambda item: -item[1]
        )[:10]:
            print(f"    {code or '(empty)'}: {count:,}")

        print("  [OK] Entire compressed file was read.")

    except Exception as exc:
        error(f"{filename}: reading or gzip validation failed: {exc}")


def check_gene_table(filename, expected_prefix):
    section(f"GENE TABLE: {filename}")
    path = RAW / filename
    ids = set()
    symbols = set()
    rows = 0
    bad_rows = 0
    duplicate_ids = 0
    invalid_ids = 0
    empty_symbols = 0

    try:
        for fields in read_tsv(path):
            if not fields or not any(fields):
                continue

            rows += 1
            if len(fields) != 3:
                bad_rows += 1
                continue

            gene_id, symbol, description = fields[:3]

            if not gene_id.startswith(expected_prefix):
                invalid_ids += 1

            if not symbol:
                empty_symbols += 1

            if gene_id in ids:
                duplicate_ids += 1
            ids.add(gene_id)
            symbols.add(symbol)

        print(f"  Rows: {rows:,}")
        print(f"  Unique IDs: {len(ids):,}")
        print(f"  Unique symbols: {len(symbols):,}")
        print(f"  Invalid ID prefixes: {invalid_ids:,}")
        print(f"  Duplicate IDs: {duplicate_ids:,}")
        print(f"  Empty symbols: {empty_symbols:,}")
        print(f"  Malformed rows: {bad_rows:,}")

        if bad_rows:
            error(f"{filename}: malformed rows.")
        if invalid_ids:
            error(f"{filename}: unexpected gene ID prefixes.")
        if duplicate_ids:
            warn(f"{filename}: duplicate gene IDs.")
        if empty_symbols:
            warn(f"{filename}: empty gene symbols.")

        return ids

    except Exception as exc:
        error(f"{filename}: {exc}")
        return set()


def check_mapping(filename, source_prefix, target_prefix):
    section(f"ORTHOLOGY TABLE: {filename}")

    rows = 0
    malformed = 0
    duplicate_rows = 0
    empty_target = 0
    invalid_source = 0
    invalid_target = 0
    source_ids = set()
    pairs = set()
    target_counts = {}
    source_counts = {}

    try:
        for fields in read_tsv(RAW / filename):
            if not fields or not any(fields):
                continue

            rows += 1
            if len(fields) != 6:
                malformed += 1
                continue

            source_id = fields[0].strip()
            target_candidates = [
                value.strip() for value in fields[2:]
                if value.strip().startswith(target_prefix)
            ]

            if not source_id.startswith(source_prefix):
                invalid_source += 1

            if not target_candidates:
                empty_target += 1
                continue

            source_ids.add(source_id)

            for target_id in target_candidates:
                pair = (source_id, target_id)
                if pair in pairs:
                    duplicate_rows += 1
                pairs.add(pair)
                source_counts[source_id] = (
                    source_counts.get(source_id, 0) + 1
                )
                target_counts[target_id] = (
                    target_counts.get(target_id, 0) + 1
                )

                if not target_id.startswith(target_prefix):
                    invalid_target += 1

        one_to_one = sum(1 for n in source_counts.values() if n == 1)
        one_to_many = sum(1 for n in source_counts.values() if n > 1)

        print(f"  Rows: {rows:,}")
        print(f"  Sources with matches: {len(source_counts):,}")
        print(f"  Unique source-target pairs: {len(pairs):,}")
        print(f"  Rows without a detected target: {empty_target:,}")
        print(f"  Sources with one match: {one_to_one:,}")
        print(f"  Sources with multiple matches: {one_to_many:,}")
        print(f"  Duplicate pairs: {duplicate_rows:,}")
        print(f"  Invalid source IDs: {invalid_source:,}")
        print(f"  Invalid target IDs: {invalid_target:,}")
        print(f"  Malformed rows: {malformed:,}")

        if malformed:
            error(f"{filename}: malformed rows.")
        if invalid_source or invalid_target:
            error(f"{filename}: unexpected ID prefixes.")
        if duplicate_rows:
            warn(f"{filename}: duplicate source-target pairs.")
        if empty_target:
            print("  Note: unmatched rows may be biologically valid.")

        return pairs

    except Exception as exc:
        error(f"{filename}: {exc}")
        return set()


def check_manifest():
    section("MANIFEST")
    path = RAW / "manifest.json"

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"  Keys: {list(data.keys())}")

        for key in ("ensembl_release", "download_date", "source", "files"):
            if key not in data:
                warn(f"Missing manifest key: {key}")

        print("  [OK] Valid JSON.")

    except Exception as exc:
        error(f"Manifest validation failed: {exc}")


def main():
    section("ORTHOLOG DETECTIVE - DEEP DATA VALIDATION")
    print(f"Project: {ROOT}")
    print(f"Raw data: {RAW}")

    section("FILE EXISTENCE")
    for name in FILES:
        path = RAW / name
        if path.is_file():
            print(f"  [OK] {name}: {path.stat().st_size:,} bytes")
        else:
            error(f"Missing file: {path}")

    if errors:
        print("\nMissing files or initial errors detected; continuing where possible.")

    if not (RAW / "go-basic.obo").is_file():
        error("Cannot continue without go-basic.obo.")
        return

    go_terms, obsolete = check_obo()

    for filename in ("HUMAN-uniprot.gaf.gz", "MOUSE-uniprot.gaf.gz"):
        if (RAW / filename).is_file():
            check_gaf(filename, go_terms, obsolete)

    if (RAW / "human_genes.tsv").is_file():
        check_gene_table("human_genes.tsv", "ENSG")

    if (RAW / "mouse_genes.tsv").is_file():
        check_gene_table("mouse_genes.tsv", "ENSMUSG")

    human_pairs = set()
    mouse_pairs = set()

    if (RAW / "human_to_mouse.tsv").is_file():
        human_pairs = check_mapping(
            "human_to_mouse.tsv", "ENSG", "ENSMUSG"
        )

    if (RAW / "mouse_to_human.tsv").is_file():
        mouse_pairs = check_mapping(
            "mouse_to_human.tsv", "ENSMUSG", "ENSG"
        )

    if human_pairs and mouse_pairs:
        section("REVERSE MAPPING CONSISTENCY")
        reverse_mouse = {(b, a) for a, b in mouse_pairs}
        common = human_pairs & reverse_mouse
        print(f"  Human-to-mouse pairs: {len(human_pairs):,}")
        print(f"  Mouse-to-human pairs: {len(mouse_pairs):,}")
        print(f"  Identical reverse pairs: {len(common):,}")
        print("  Note: differences can arise from source filtering or release.")

    if (RAW / "manifest.json").is_file():
        check_manifest()

    section("FINAL SUMMARY")
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("[CHECK] Review errors before using the data.")
        sys.exit(1)
    elif warnings:
        print("[PASS WITH WARNINGS] No critical format errors detected.")
    else:
        print("[PASS] No issues detected by these checks.")


if __name__ == "__main__":
    main()