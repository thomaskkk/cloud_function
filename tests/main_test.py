import src.main as main
import pytest

def test_config_is_generated_from_json_request_body(input_json: str):
    # Given
    # When
    error = main.test_config(input_json)

    # Then
    assert error is None

