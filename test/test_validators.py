from cspark.sdk import SparkError
from cspark.sdk.validators import Validators


def test_invalid_empty_string():
    validator = Validators.empty_str()
    assert validator.is_valid(None) is False
    assert validator.is_valid('') is False
    assert validator.is_valid(' ') is False
    assert len(validator.errors) == 3
    assert all(isinstance(error, SparkError) for error in validator.errors)


def test_reset_errors():
    validator = Validators.positive_int()
    assert validator.is_valid(-1) is False
    assert validator.is_valid(0) is False
    assert len(validator.errors) == 2

    validator.reset()
    assert len(validator.errors) == 0


def test_auto_reset_errors_upon_new_instances():
    validator = Validators.base_url()
    assert not validator.is_valid('http://incorrect-url')
    assert len(validator.errors) == 1

    validator = Validators.base_url()
    assert len(validator.errors) == 0
