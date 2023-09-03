import pytest
import json

@pytest.fixture(scope="module")
def input_json():
    input_json = '''
{
    "Account_number": 12345,
    "Report_number": 1234567,
    "Report_token": "largest_token_ever_123",
    "Cycletime": {
        "Percentiles": [
            50,
            85,
            95
        ]
    },
    "Throughput_range": 90,
    "Montecarlo": {
        "Simulations": 10000,
        "Simulation_days": 14,
        "Percentiles": [
            50,
            85,
            95
        ]
    }
}
'''
    return json.loads(input_json)

