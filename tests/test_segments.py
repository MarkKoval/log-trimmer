from core.segments import (
    Segment,
    SegmentError,
    add_remove_segment,
    normalize_segments,
    trim_to_selection,
    validate_segments,
)


def test_normalize_segments_merges_overlaps() -> None:
    segments = [Segment(0, 2), Segment(1, 3), Segment(4, 5)]
    normalized = normalize_segments(segments)
    assert normalized == [Segment(0, 3), Segment(4, 5)]


def test_trim_to_selection_produces_remove_segments() -> None:
    remove_segments = trim_to_selection((0, 10), Segment(3, 7))
    assert remove_segments == [Segment(0, 3), Segment(7, 10)]


def test_add_remove_segment_merges() -> None:
    segments = [Segment(0, 2)]
    updated = add_remove_segment(segments, Segment(1, 3))
    assert updated == [Segment(0, 3)]


def test_validate_segments_rejects_out_of_range() -> None:
    try:
        validate_segments([Segment(-1, 2)], (0, 10))
    except SegmentError:
        assert True
    else:
        assert False
