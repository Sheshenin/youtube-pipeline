from pipeline.shorts import is_short_duration


def test_is_short_duration():
    assert is_short_duration("PT45S") is True
    assert is_short_duration("PT1M05S") is False
    assert is_short_duration("PT12M") is False
    assert is_short_duration("") is False
    assert is_short_duration(None) is False
