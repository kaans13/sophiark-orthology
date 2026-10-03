def compare_sets(a: set, b: set) -> dict:
    """Set-based annotation overlap. Jaccard is None when both sets are empty."""
    a, b = set(a), set(b)
    union = a | b
    return {
        "shared": sorted(a & b),
        "source_only": sorted(a - b),
        "target_only": sorted(b - a),
        "jaccard": (len(a & b) / len(union)) if union else None,
    }
