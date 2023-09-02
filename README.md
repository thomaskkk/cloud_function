
# Jira metrics Eazybi Cloud functions
This a simple API that captures a public report from Eazybi and do calculations to output the Monte Carlo forecast metrics to be imported to Eazybi source.

The output could be, for example: How many itens the team could deliver in 14 days with 85% cofidence(percentile)?

This is a alternative version to Jira metrics Eazybi that can be deployed to a cloud function.
## How to use
### Eazybi public report
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

Save the report and make it public with an access token.

### Configuration
You can add your configuration using GCP enviroment variables or you can also add a real config file as an alternative you can use GCP Secret Manager to emulate a config file.

You can have multiple Secrets (entries/filenames) for multiple Eazybi accounts, for example each one representing one squad.

#### GCP Secret Manager as enviroment variables
- Open `config_file_sample.yml` and paste all info from the public report: Account_number, Report_number, Report_token
- Check for any further changes necessary to the yaml file.
- Use the GCP Secret Manager to create a secret and paste the contents of the updated `config_file_sample.yml` structure.
- You can safely delete the `config_file_sample.yml`
- When deploying your Cloud function make the secret accessible from a enviroment variable.
- Give permissions for your Cloud function to access your secret.

#### Config file / GCP Secret Manager emulating a config file
- Open config_file_sample.yml and paste all info from the public report: Account_number, Report_number, Report_token
- Check for any further changes necessary to the yaml file.
- Copy the file to `secrets/<desired_config_filename>.yml`
- As an alternative you can configure GCP Secret Manager to emulate a file.

### Cloud function creation
To create you cloud function:
- Set up your secret make it avaliable using instructions above.
- Paste the contents from `main.py` in the `src/` dir to your cloud function file.
- Paste the contents from `requirements.txt`.
- Define your entrypoint as `main`.


### Configure API Eazybi project
Go to your account Source Data tab and add a new source aplication as a `Rest:API`.
- Your source data URL should be <your_gcp_server_url>/eazybi/<your_secret_name_or_config_filename_without_.yml>
    - Example: https://jira-metrics-eazybi.app/eazybi/jp
- Set request method to `POST`
- Add to the request body a single json entry title `squad` with value `secret_name`
```json
{
    "squad": "secret_name"
}
```
- Content type to `JSON`
- Data path to `$.data`

## How to setup dev enviroment
### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
`launch.json` is a sample file to be able to debug locally in vscode,add it to your `.vscode` dir.

To be able to generate http requests Postman vscode extension is recommended.