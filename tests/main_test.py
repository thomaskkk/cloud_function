import src.main as main
import json


def test_config_is_generated_from_json_request_body(input_json: str):
    # Given
    dict_json = json.loads(input_json)

    # When
    error = main.test_config(input_json)

    # Then
    assert error is None

def test_url_generates_from_config_json():
    # Given


    # When
    
    # Then
    assert True
