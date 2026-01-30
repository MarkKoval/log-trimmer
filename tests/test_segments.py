import pytest

from core.segments import Segment, normalize_segments, remove_segments, validate_segments


def test_normalize_segments_merges_overlaps():
    segments = [Segment(1, 3), Segment(2, 4), Segment(5, 6)]
    merged = normalize_segments(segments)
    assert merged == [Segment(1, 4), Segment(5, 6)]


def test_remove_segments_builds_keep_ranges():
    remove = [Segment(2, 4), Segment(6, 7)]
    keep = remove_segments(0, 10, remove)
    assert keep == [Segment(0, 2), Segment(4, 6), Segment(7, 10)]


def test_validate_segments_bounds():
    with pytest.raises(ValueError):
        validate_segments([Segment(5, 3)], 0, 10)
    with pytest.raises(ValueError):
        validate_segments([Segment(-1, 2)], 0, 10)
