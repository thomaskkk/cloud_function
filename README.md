
# Jira metrics Eazybi Cloud functions
This a simple API that captures a public report from Eazybi and do calculations to output the Monte Carlo forecast metrics to be imported to Eazybi source.

The output could be, for example: How many itens the team could deliver in 14 days with 85% cofidence(percentile)?

This is a alternative version to [Jira metrics Eazybi](https://github.com/thomaskkk/jira_metrics_eazybi) that can be deployed to a GCP Cloud Function.

Sample output:
```json
{
    "schema": {
        "fields": [
            {
                "name": "project",
                "type": "string"
            },
            {
                "name": "cycletime 50%",
                "type": "integer"
            },
            {
                "name": "cycletime 85%",
                "type": "integer"
            },
            {
                "name": "cycletime 95%",
                "type": "integer"
            },
            {
                "name": "montecarlo 50%",
                "type": "integer"
            },
            {
                "name": "montecarlo 85%",
                "type": "integer"
            },
            {
                "name": "montecarlo 95%",
                "type": "integer"
            }
        ],
        "primaryKey": [
            "project"
        ],
        "pandas_version": "1.4.0"
    },
    "data": [
        {
            "project": "JP",
            "cycletime 50%": 3,
            "cycletime 85%": 14,
            "cycletime 95%": 29,
            "montecarlo 50%": 18,
            "montecarlo 85%": 12,
            "montecarlo 95%": 9
        }
    ]
}
```
## How to use
### Setup an Eazybi public report
Create an Eazybi report to be consumed by this api, example:
- Rows
    - Project dimension, Project hierarchy level
    - Time dimension, Day hierarchy level
    - Issue dimension, Issue hierarchy level
- Columns
    - Measure cycle time (in days)

Your table/data should look like this:

| Project | Time | Issue | Cycle time |
| ----------- | ----------- | ----------- | ----------- |
| JP | Aug 25 2022 | JP-105 | 24
| JP | Aug 29 2022 | JP-110 | 30

Save the report and make it public with an access token, you will use this info in the request Json body.

### Setup a GCP Cloud function
Create a runtime enviroment variable with the name `AUTH_BEARER_TOKEN` with a secret token of your choice

You should configure the cloud function as usual copying `main.py` and `requirements.txt` and define the entrypoint as `main`

### Configure API Eazybi project
Go to your account Source Data tab and add a new source aplication as a `Rest:API`.
- Your source data URL should be <your_gcp_server_url>/eazybi/<your_secret_name_or_config_filename_without_.yml>
    - Example: https://jira-metrics-eazybi.app/eazybi/jp
- Set request method to `POST`
- Add to the request body the report details and calculation configuration:
```json
{
    "Account_number": "Eazybi report account number, integer (without quotes)",
    "Report_number": "Eazybi report number, integer (without quotes)",
    "Report_token": "Eazybi report token, string (WITH quotes)",
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
```
- Set Authentication parameters as `HTTP header`
    - Header name `Authorization`
    - Header value the token created as an eviroment varialbe on your cloud function
- Content type to `JSON`
- Data path to `$.data`

## How to setup dev enviroment
### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt
```
`launch.json` is a sample file to be able to debug locally in vscode,add it to your `.vscode` dir.

To be able to generate http requests Postman vscode extension is recommended.

You can create a enviroment variable creating a `.env` file.