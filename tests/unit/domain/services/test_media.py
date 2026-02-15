from brain.domain.services.media import get_file_extension


def test_get_file_extension_returns_lowercase_extension():
    assert get_file_extension("report.PDF") == "pdf"


def test_get_file_extension_returns_default_when_missing_extension():
    assert get_file_extension("README") == "bin"


def test_get_file_extension_returns_custom_default():
    assert get_file_extension(None, default="txt") == "txt"
