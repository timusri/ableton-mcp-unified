"""Index, bar/beat and response-rewrite helpers."""
import pytest

from ableton_mcp.convert import (_optional_to_zero_based, _to_zero_based, bar_to_beat, beat_to_bar,
                                 denormalize_param, normalize_param, params_to_zero_based, to_one_based)


class TestToZeroBased:
    def test_converts(self):
        assert _to_zero_based(1) == 0
        assert _to_zero_based(5) == 4

    def test_rejects_zero_and_negative(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            _to_zero_based(0)
        with pytest.raises(ValueError, match="track_index must be >= 1"):
            _to_zero_based(-1, "track_index")


class TestOptionalToZeroBased:
    def test_zero_means_unset(self):
        assert _optional_to_zero_based(0) is None

    def test_converts(self):
        assert _optional_to_zero_based(3) == 2

    def test_rejects_negative(self):
        with pytest.raises(ValueError):
            _optional_to_zero_based(-2)


class TestBarBeat:
    def test_4_4(self):
        assert bar_to_beat(1) == 0.0
        assert bar_to_beat(5) == 16.0
        assert beat_to_bar(16.0) == 5

    def test_3_4(self):
        assert bar_to_beat(5, 3, 4) == 12.0
        assert beat_to_bar(12.0, 3, 4) == 5

    def test_6_8(self):
        assert bar_to_beat(2, 6, 8) == 3.0


class TestNormalize:
    def test_roundtrip(self):
        assert normalize_param(50.0, 0.0, 100.0) == 0.5
        assert denormalize_param(0.5, 0.0, 100.0) == 50.0

    def test_clamps(self):
        assert normalize_param(150.0, 0.0, 100.0) == 1.0
        assert denormalize_param(2.0, 0.0, 100.0) == 100.0

    def test_degenerate_range(self):
        assert normalize_param(5.0, 5.0, 5.0) == 0.0


class TestToOneBased:
    def test_rewrites_index_keys_recursively(self):
        data = {"index": 0, "track_index": 2, "devices": [{"index": 1, "name": "x"}], "note": 36, "count": 3}
        out = to_one_based(data)
        assert out["index"] == 1
        assert out["track_index"] == 3
        assert out["devices"][0]["index"] == 2
        assert out["note"] == 36
        assert out["count"] == 3

    def test_leaves_sentinels_alone(self):
        assert to_one_based({"playing_slot_index": -1})["playing_slot_index"] == -1
        assert to_one_based({"fired_slot_index": -2})["fired_slot_index"] == -2

    def test_index_lists(self):
        assert to_one_based({"track_indices": [0, 2]})["track_indices"] == [1, 3]

    def test_does_not_touch_bools_or_floats(self):
        assert to_one_based({"index": True}) == {"index": True}
        assert to_one_based({"index": 1.5}) == {"index": 1.5}


class TestParamsToZeroBased:
    def test_converts_index_suffix(self):
        assert params_to_zero_based({"track_index": 1, "clip_index": 3, "value": 0.5}) == {
            "track_index": 0, "clip_index": 2, "value": 0.5}

    def test_keeps_append_sentinel(self):
        assert params_to_zero_based({"index": -1}) == {"index": -1}

    def test_lists(self):
        assert params_to_zero_based({"track_indices": [1, 2]}) == {"track_indices": [0, 1]}

    def test_rejects_zero(self):
        with pytest.raises(ValueError):
            params_to_zero_based({"track_index": 0})
