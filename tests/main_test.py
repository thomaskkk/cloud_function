import src.main as main
import json

def test_config_is_generated_from_json_request_body(cfg_json: str):
    # Given
    # When
    error = main.test_config(cfg_json)

    # Then
    assert error is None

def test_url_generates_from_config_json(cfg_json):
    # Given
    # When
    url = main.generate_url(cfg_json)
    
    # Then
    assert url == "https://aod.eazybi.com/accounts/12345/export/report/1234567-api-export.csv?embed_token=largest_token_ever_123"


