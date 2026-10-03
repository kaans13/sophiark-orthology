"""Search raw GAF lines for a symbol substring (case-insensitive), print up to N matches.

Usage: python scripts/grep_gaf.py goa_mouse.gaf.gz Trp53
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR  # noqa: E402
from src.ingestion.go import iter_gaf_lines  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: python scripts/grep_gaf.py goa_mouse.gaf.gz Trp53\n"
                  "   or: python scripts/grep_gaf.py goa_mouse.gaf.gz uniprot:P02340")
    fname, needle_raw = sys.argv[1], sys.argv[2]
    path = RAW_DIR / "go" / fname

    if needle_raw.lower().startswith("uniprot:"):
        target_id = needle_raw.split(":", 1)[1]
        n_lines, matches = 0, []
        for line in iter_gaf_lines(path):
            n_lines += 1
            cols = line.split("\t")
            if len(cols) > 1 and cols[1] == target_id:
                matches.append(line)
        print(f"Scanned {n_lines} lines. {len(matches)} lines with DB_Object_ID={target_id!r}")
        for line in matches[:10]:
            print(f"  {line[:160]}")
        return

    needle = needle_raw.lower()
    exact, substring = [], []
    n_lines = 0
    for line in iter_gaf_lines(path):
        n_lines += 1
        cols = line.split("\t")
        symbol = cols[2] if len(cols) > 2 else ""
        sym_lower = symbol.lower()
        if sym_lower == needle:
            exact.append((symbol, line))
        elif needle in sym_lower:
            substring.append((symbol, line))

    print(f"Scanned {n_lines} lines.")
    print(f"\nExact symbol matches (case-insensitive) for {needle!r}: {len(exact)}")
    for symbol, line in exact[:10]:
        print(f"  symbol={symbol!r}  line={line[:160]}")

    print(f"\nSubstring matches (other genes containing {needle!r}): "
          f"{len(substring)} distinct lines, symbols: "
          f"{sorted(set(s for s, _ in substring))[:15]}")


if __name__ == "__main__":
    main()