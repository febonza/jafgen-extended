import csv
import os

from jafgen.cli import _seed_all
from jafgen.simulation import Simulation

SIM_DAYS = 7


def _run(tmp_path, seed=None):
    if seed is not None:
        _seed_all(seed)
    tmp_path.mkdir(parents=True, exist_ok=True)
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        sim = Simulation(0, SIM_DAYS, "raw")
        sim.run_simulation()
        sim.save_results()
        with open(tmp_path / "jaffle-data" / "raw_orders.csv") as f:
            return list(csv.DictReader(f))
    finally:
        os.chdir(orig)


def test_same_seed_produces_identical_output(tmp_path):
    orders_a = _run(tmp_path / "a", seed=42)
    orders_b = _run(tmp_path / "b", seed=42)
    assert orders_a == orders_b


def test_different_seeds_produce_different_output(tmp_path):
    orders_a = _run(tmp_path / "a", seed=42)
    orders_b = _run(tmp_path / "b", seed=99)
    assert orders_a != orders_b
