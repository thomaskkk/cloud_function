import functions_framework
import os
import confuse
import yaml
import pandas as pd
import numpy as np
from datetime import date, timedelta

cfg = confuse.Configuration('MyGreatApp', __name__)

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
    request_dict = request.get_json()
    config(request_dict.get("squad"))
    report_url = generate_url()
    kanban_data = get_eazybi_report(report_url)
    ct = calc_cycletime_percentile(kanban_data)
    today = date.today().strftime("%Y-%m-%d")
    past = date.today() - timedelta(days=cfg["Throughput_range"].get())
    past = past.strftime("%Y-%m-%d")
    tp = calc_throughput(kanban_data, past, today)
    mc = run_simulation(tp)
    mc = mc.rename(index={"issues": kanban_data.loc[0]["project"]})
    result = ct.merge(mc, left_index=True, right_index=True)

    return result.to_json(orient="table")


def config(squad):
        """Set config based on files or enviroment variables"""
        if os.path.isfile("secrets/" + str(squad) + ".yml"):
            cfg.set_file("secrets/" + str(squad) + ".yml")
        elif os.environ.get(squad):
            yaml_string =  os.environ.get(squad)
            yaml_data = yaml.load(yaml_string, Loader=yaml.FullLoader)
            cfg.set(yaml_data)
        else:
            return {
                "message": {
                    "filename": "You don't have any valid config files",
                }
            }

def generate_url():
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

def calc_cycletime_percentile(kanban_data, percentile=None):
    """Calculate cycletime percentiles on cfg with all dict entries"""
    if kanban_data.empty is False:
        if percentile is not None:
            issuetype = (
                kanban_data.groupby("project")
                .cycletime.quantile(percentile / 100)
                .apply(np.ceil)
                .astype("int")
            )
            return issuetype
        else:
            cycletime = None
            for cfg_percentile in cfg["Cycletime"]["Percentiles"].get():
                temp_cycletime = (
                    kanban_data.groupby("project")
                    .cycletime.quantile(cfg_percentile / 100)
                    .rename("cycletime " + str(cfg_percentile) + "%")
                    .apply(np.ceil)
                    .astype("int")
                )
                if cycletime is None:
                    cycletime = temp_cycletime.to_frame()
                else:
                    cycletime = cycletime.merge(
                        temp_cycletime, left_index=True, right_index=True
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

def run_simulation(throughput, simul=None, simul_days=None):
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
        simul = cfg["Montecarlo"]["Simulations"].get()
    if simul_days is None:
        simul_days = cfg["Montecarlo"]["Simulation_days"].get()

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
        for percentil in cfg["Montecarlo"]["Percentiles"].get():
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