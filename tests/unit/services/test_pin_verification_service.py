import pytest

from brain.application.services.pin_verification import (
    InvalidPinFormatException,
    PinVerificationService,
)


def test_hash_pin_creates_non_plaintext_hash():
    service = PinVerificationService()

    pin_hash = service.hash_pin("1234")

    assert pin_hash
    assert pin_hash != "1234"


def test_verify_pin_returns_true_for_matching_pin():
    service = PinVerificationService()
    pin_hash = service.hash_pin("1234")

    result = service.verify_pin("1234", pin_hash)

    assert result is True


def test_verify_pin_returns_false_for_non_matching_pin():
    service = PinVerificationService()
    pin_hash = service.hash_pin("1234")

    result = service.verify_pin("0000", pin_hash)

    assert result is False


def test_hash_pin_raises_for_invalid_pin_format():
    service = PinVerificationService()

    with pytest.raises(InvalidPinFormatException):
        service.hash_pin("12ab")


def test_verify_pin_raises_for_invalid_pin_format():
    service = PinVerificationService()

    with pytest.raises(InvalidPinFormatException):
        service.verify_pin("12ab", "hash")
