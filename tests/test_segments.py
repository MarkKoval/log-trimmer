import pytest

from core.segments import Segment, SegmentError, apply_cut, apply_trim, invert_segments


def test_invert_segments_basic():
    segments = [Segment(2, 4), Segment(6, 7)]
    inverted = invert_segments(segments, 0, 10)
    assert inverted == [Segment(0, 2), Segment(4, 6), Segment(7, 10)]


def test_trim_produces_remove_segments():
    remove = apply_trim(Segment(3, 8), 0, 10)
    assert remove == [Segment(0, 3), Segment(8, 10)]


def test_cut_merges_overlaps():
    remove = apply_cut([Segment(1, 4), Segment(3, 6)], 0, 10)
    assert remove == [Segment(1, 6)]


def test_invalid_segment_raises():
    with pytest.raises(SegmentError):
        apply_trim(Segment(5, 5), 0, 10)
