import functions_framework
import jsonschema
import pandas as pd
import numpy as np
from datetime import date, timedelta

@functions_framework.http
def main(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    Note:
        For more information on how Flask integrates with Cloud
        Functions, see the `Writing HTTP functions` page.
        <https://cloud.google.com/functions/docs/writing/http#http_frameworks>
    """
    cfg = request.get_json()
    config_error = test_config(cfg)
    if config_error:
        return config_error
    else:
        report_url = generate_url(cfg)
        kanban_data = get_eazybi_report(report_url)
        ct = calc_cycletime_percentile(cfg, kanban_data)
        today = date.today().strftime("%Y-%m-%d")
        past = date.today() - timedelta(days=cfg["Throughput_range"])
        past = past.strftime("%Y-%m-%d")
        tp = calc_throughput(kanban_data, past, today)
        mc = run_simulation(cfg, tp)
        mc = mc.rename(index={"issues": kanban_data.loc[0]["project"]})
        result = ct.merge(mc, left_index=True, right_index=True)

        return result.to_json(orient="table")


def test_config(cfg):
        """Test config from json body"""
        validationSchema = {
            "type": "object",
            "properties": {
                "Account_number": {"type": "integer"},
                "Report_number": {"type": "integer"},
                "Report_token": {"type": "string"},
                "Cycletime": {
                    "type": "object",
                    "properties": {
                        "Percentiles": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            },
                            "minItems": 1,
                            "maxItems": 5
                        }
                    },
                    "required": ["Percentiles"],
                    "minProperties": 1,
                    "maxProperties": 1
                },
                "Throughput_range": {"type": "integer"},
                "Montecarlo": {
                    "type": "object",
                    "properties": {
                        "Simulations": {"type": "integer"},
                        "Simulation_days": {"type": "integer"},
                        "Percentiles": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            },
                            "minItems": 1,
                            "maxItems": 5
                        }
                    },
                    "required": ["Simulations", "Simulation_days", "Percentiles"],
                    "minProperties": 3,
                    "maxProperties": 3
                }
            },
            "required": ["Account_number", "Report_number", "Report_token", "Cycletime", "Throughput_range",  "Montecarlo"],
            "minProperties": 6,
            "maxProperties": 6

        }
        
        try:
            jsonschema.validate(instance=cfg, schema=validationSchema)
        except jsonschema.exceptions.ValidationError as err:
            return {
                "message": {
                    "json_body": "You invalid entries in config Json",
                }
            }

def generate_url(cfg):
    """Generate a url to fetch eazybi data"""
    url = (
        "https://aod.eazybi.com/accounts/"
        + str(cfg["Account_number"])
        + "/export/report/"
        + str(cfg["Report_number"])
        + "-api-export.csv?embed_token="
        + str(cfg["Report_token"])
    )
    return url

def get_eazybi_report(report_url):
    """Capture eazybi data from an url and convert to a dictionary"""
    dictio = pd.read_csv(report_url, delimiter=",", parse_dates=["Time"])
    dictio.columns = ["project", "date", "issue", "cycletime"]
    return dictio

def calc_cycletime_percentile(cfg, kanban_data, percentile=None):
    """Calculate cycletime percentiles on cfg with all dict entries"""
    if not kanban_data.empty:
        cycletime = None
        for cfg_percentile in cfg["Cycletime"]["Percentiles"]:
            temp_cycletime = (
                kanban_data.groupby("project")
                .cycletime.quantile(cfg_percentile / 100)
                .rename("cycletime " + str(cfg_percentile) + "%")
                .apply(np.ceil)
                .astype("int")
            )
            if cycletime is None:
                cycletime = pd.DataFrame(temp_cycletime)
            else:
                cycletime = pd.merge(
                    cycletime, temp_cycletime, left_index=True, right_index=True
                )
        return cycletime

def calc_throughput(kanban_data, start_date=None, end_date=None):
    """Change the pandas DF to a Troughput per day format, a good
    throughput table has all days from start date to end date filled
    with zeroes if there are no ocurrences

    Parameters
    ----------
        kanban_data : dataFrame
            dataFrame to be sorted by throughput (number of ocurrences
            per day)
        start_date : date
            earliest date of the throughput
        end_date : date
            final date of the throughput
    """
    if start_date is not None and "date" in kanban_data.columns:
        kanban_data = kanban_data[~(kanban_data["date"] < start_date)]
    if end_date is not None and "date" in kanban_data.columns:
        kanban_data = kanban_data[~(kanban_data["date"] > end_date)]
    if kanban_data.empty is False:
        # Reorganize DataFrame
        throughput = pd.crosstab(
            kanban_data.date, columns=["issues"], colnames=[None]
        ).reset_index()
        if throughput.empty is False and (
            start_date is not None and end_date is not None
        ):
            date_range = pd.date_range(start=start_date, end=end_date)
            throughput = (
                throughput.set_index("date")
                .reindex(date_range)
                .fillna(0)
                .astype(int)
                .rename_axis("Date")
            )
        return throughput

def run_simulation(cfg, throughput, simul=None, simul_days=None):
    """Run monte carlo simulation with the result of how many itens will
    be delivered in a set of days

    Parameters
    ----------
        throughput : dataFrame
            throughput base values of the simulation
        simul : integer
            number of simulations
        simul_days : integer
            days to run the simulation
    """
    if simul is None:
        simul = cfg["Montecarlo"]["Simulations"]
    if simul_days is None:
        simul_days = cfg["Montecarlo"]["Simulation_days"]

    mc = None
    if throughput is not None:
        dataset = throughput[["issues"]].reset_index(drop=True)
        samples = [
            getattr(dataset.sample(n=simul_days, replace=True).sum(), "issues")
            for i in range(simul)
        ]
        samples = pd.DataFrame(samples, columns=["Items"])
        distribution = (
            samples.groupby(["Items"]).size().reset_index(name="Frequency")
        )
        distribution = distribution.sort_index(ascending=False)
        distribution["Probability"] = (
            100 * distribution.Frequency.cumsum()
        ) / distribution.Frequency.sum()
        mc_results = {}
        # Get nearest neighbor result
        for percentil in cfg["Montecarlo"]["Percentiles"]:
            result_index = distribution["Probability"].sub(percentil).abs().idxmin()
            mc_results["montecarlo " + str(percentil) + "%"] = distribution.loc[
                result_index, "Items"
            ]
        if mc is None:
            mc = pd.DataFrame.from_dict(
                mc_results, orient="index", columns=["issues"]
            ).transpose()
        else:
            temp_mc = pd.DataFrame.from_dict(
                mc_results, orient="index", columns=["issues"]
            ).transpose()
            mc = pd.concat([mc, temp_mc])
    else:
        return None
    return mc