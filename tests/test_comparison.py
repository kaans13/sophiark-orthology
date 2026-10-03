from src.analysis.overlap import compare_sets


def test_shared_source_target_only():
    r = compare_sets({"a", "b"}, {"b", "c"})
    assert r["shared"] == ["b"]
    assert r["source_only"] == ["a"]
    assert r["target_only"] == ["c"]


def test_jaccard():
    assert compare_sets({"a", "b"}, {"b", "c"})["jaccard"] == 1 / 3


def test_both_empty_is_none():
    assert compare_sets(set(), set())["jaccard"] is None


def test_one_empty_is_zero():
    assert compare_sets({"a"}, set())["jaccard"] == 0.0
