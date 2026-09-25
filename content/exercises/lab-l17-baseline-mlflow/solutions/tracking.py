"""Local MLflow tracking for lab L17: a file store inside a temporary directory, never a server.

Three environment settings are made here, before mlflow is imported, so every module that imports
this one inherits them:

* MLFLOW_ALLOW_FILE_STORE=true. MLflow 3.16.1 raises an MlflowException when a filesystem tracking
  or registry backend is instantiated without it: the file store is in maintenance mode and the
  documented migration target is a database backend such as sqlite. The lab keeps the file store on
  purpose: it needs no server and no database, a learner can open the run record as plain files,
  and the whole directory is deleted at the end of every run.
* MLFLOW_DISABLE_TELEMETRY=true and DO_NOT_TRACK=true. MLflow 3.16.1 collects usage telemetry by
  default; the lab runs offline and sends nothing.
* MLFLOW_DISABLE_AGENT_HINT=1 silences an informational hint printed at import.

Two MLflow UserWarnings are filtered, both explained where they are filtered: the dataset-source
resolution notice for a relative path, and the integer-column hint for the logged dataset schema
(the model's own inputs are cast to float64 before the signature is inferred).
"""
import os
import shutil
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
os.environ.setdefault("DO_NOT_TRACK", "true")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow  # noqa: E402

# The dataset source is recorded as the relative text "fixtures/oven_days.csv"; MLflow can read that
# text as more than one local source type and warns before choosing one. The digest does not depend
# on the source text (checked in the lab), so the notice carries no information here.
warnings.filterwarnings("ignore", message="The specified dataset source can be interpreted in multiple ways")
# The logged dataset keeps the fixture's integer columns (day, door_cycles, the label). MLflow hints
# that integer columns cannot hold missing values; the model's inputs are float64 and the fixture
# has no missing values, so the hint is about a problem this dataset does not have.
warnings.filterwarnings("ignore", message="Hint: Inferred schema contains integer column")

EXPERIMENT_NAME = "cinderline-oven-fault-warning"


@contextmanager
def tracking_directory(prefix="l17-mlflow-", keep=False):
    """Create a temporary directory, point tracking (and so the registry) at its "tracking" folder,
    and delete the whole directory afterwards.

    The file store reads every folder under its root as an experiment, so files the lab writes
    (the contract, the decision file) go next to the store, never inside it. The previous tracking
    URI is restored on exit. Reading it has no side effect: in MLflow 3.16.1 the default is a sqlite
    file in the working directory, which is only created when a store is actually used.
    """
    previous = mlflow.get_tracking_uri()
    root = Path(tempfile.mkdtemp(prefix=prefix))
    store = root / "tracking"
    store.mkdir()
    mlflow.set_tracking_uri(store.as_uri())
    try:
        yield root
    finally:
        mlflow.set_tracking_uri(previous)
        if not keep:
            shutil.rmtree(root, ignore_errors=True)


def experiment_id(name=EXPERIMENT_NAME):
    """Return the experiment's id, creating the experiment on first use."""
    existing = mlflow.get_experiment_by_name(name)
    return existing.experiment_id if existing else mlflow.create_experiment(name)
