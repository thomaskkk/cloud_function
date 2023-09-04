import src.main as main
import pandas as pd

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

def test_calc_cycletime_percentile_single_project():
    # Given
    cfg = {
        "Cycletime": {
            "Percentiles": [50, 75, 90]
        }
    }
    kanban_data = pd.DataFrame({
        "project": ["JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP", "JP"],
        "cycletime": [5, 7, 10, 12, 40, 23, 2, 21, 5, 66, 22, 15, 27, 38]
    })
    expected_result = pd.DataFrame({
        "cycletime 50%": [18],
        "cycletime 75%": [26],
        "cycletime 90%": [40]
    }, index=["JP"])

    # When
    result = main.calc_cycletime_percentile(cfg, kanban_data)

    # Then
    assert result.equals(expected_result)

def test_valid_dataframe_with_date_and_issue_columns():
    # Given - Create a valid pandas dataframe with date and issue columns
    kanban_data = pd.DataFrame({
        'date': ['2021-01-01', '2021-01-01', '2021-01-02', '2021-01-03'],
        'issue': ['JP-1', 'JP-2', 'JP-3', 'JP-4']
    })

    # When - Call the calc_throughput function
    throughput = main.calc_throughput(kanban_data)

    # Then - Assert that the throughput dataframe is correct
    expected_throughput = pd.DataFrame({
        'date': ['2021-01-01', '2021-01-02', '2021-01-03'],
        'issues': [2, 1, 1]
    })
    pd.testing.assert_frame_equal(throughput, expected_throughput)
