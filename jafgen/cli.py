import datetime as dt
from typing import Annotated, Optional

import typer

from jafgen.simulation import Simulation
from jafgen.time import Day

app = typer.Typer()


def _parse_date(value: Optional[str], flag: str) -> Optional[dt.date]:
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(
            f"'{value}' is not a valid ISO date (expected YYYY-MM-DD)",
            param_hint=f"'{flag}'",
        )


@app.command()
def run(
    # We set default to 0 here to make sure users don't get confused if they only put in days.
    # If they don't set anything we have years default = 1 later to keep the same functionality.
    years: Annotated[
         int, typer.Argument(help="Number of years to simulate. If neither days nor years are provided, the default is 1 year.")
    ] = 0,
    days: Annotated[
        int, typer.Option(help="Number of days to simulate. Default is 0.")
    ] = 0,
    pre: Annotated[
        str,
        typer.Option(help="Optional prefix for the output file names."),
    ] = "raw",
    center_on: Annotated[
        Optional[str],
        typer.Option(
            help="Shift all output dates so the simulation starts on this date (YYYY-MM-DD).",
        ),
    ] = None,
    export_from: Annotated[
        Optional[str],
        typer.Option(
            help="Exclude rows with dates before this date from orders and tweets (YYYY-MM-DD).",
        ),
    ] = None,
) -> None:

    # To keep the default value for backwards compatibility.
    if years == 0 and days == 0:
        years = 1

    center_on_date = _parse_date(center_on, "--center-on")
    export_from_date = _parse_date(export_from, "--export-from")

    sim = Simulation(years, days, pre)

    if center_on_date is not None and export_from_date is not None and export_from_date < center_on_date:
        raise typer.BadParameter(
            f"--export-from ({export_from_date}) must not be before --center-on ({center_on_date})",
            param_hint="'--export-from'",
        )

    epoch_date = Day.EPOCH.date()
    effective_start = center_on_date if center_on_date is not None else epoch_date
    sim_end_date = effective_start + dt.timedelta(days=sim.sim_days - 1)

    if export_from_date is not None and export_from_date > sim_end_date:
        raise typer.BadParameter(
            f"--export-from ({export_from_date}) is after the simulation end date ({sim_end_date})",
            param_hint="'--export-from'",
        )

    sim.run_simulation()
    sim.save_results(center_on=center_on_date, export_from=export_from_date)
