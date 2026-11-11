# Copilot instructions for FastAPI_Rapprochement_mkajy

## Project overview
This repository is a Python ETL and reconciliation pipeline for daily transaction processing. The workflow reads source transaction extracts, normalizes them, stores staged Excel files under `staggingArea/`, reconciles OM and AMS data, and writes output reports to `output/reconciliation/` before pushing matched data into SQL Server.

Key entry points:
- `apiServer.py` exposes a FastAPI application with endpoints for all pipeline stages, including `transformTangoTransaction`, `transformPicoTransaction`, `transformOMTransaction`, `transformAMS`, `generateOMMapping`, `generateFrontTrx`, `generateGLTrx`, `reconcile`, `upload_reconciliation`, and `check_unreconciled_transaction`. The `GET /input-file?relative_path=file.xls` endpoint downloads a file from `input/TANGO/`.
- `mainTango.py`, `mainPICO.py`, `mainOM.py`, and `mainAMS.py` perform the daily staged ETL steps.
- `reconciliation.py` contains the matching logic between AMS and OM transactions using amount, type, and time-window filters.
- `ETL.py` and `Check_transaction_before_reconciliation.py` handle SQL Server loads and unreconciled-transaction checks.

The high-level flow matches the project README:
1. `mainTango` cleans Tango transactions and stores them in staging.
2. `mainPICO` cleans PICO transactions and stores them in staging.
3. `mainOM` merges the cleaned evidence into a daily OM dataset.
4. `mainAMS` extracts AMS transactions from the source system.
5. `generateOM_Transaction` and `generatePAMF_Transaction` build downstream transaction files.
6. `reconciliation.py` performs the final matching and status checks.

## Build, test, and lint commands
This repository does not currently include a formal Python project config, test suite, or linter configuration (`pytest`, `tox`, `ruff`, `flake8`, etc. were not found).

Use the repo as a script-based ETL project instead of a package-style app:
- Start the API locally:
  `python -m uvicorn apiServer:app --host 0.0.0.0 --port 8000`
- Run a single ETL step directly in Python:
  `python -c "from datetime import date; from mainTango import ETL_TANGO; print(ETL_TANGO(date(2026, 3, 24)))"`
- Run the unreconciled check directly:
  `python -c "from datetime import date; from Check_transaction_before_reconciliation import check_unreconciled_transaction; print(check_unreconciled_transaction(date(2026, 3, 24)))"`
- For focused validation, prefer the smallest relevant script or endpoint over running the whole pipeline.

## Key conventions
- This repo is organized as a set of scripts, not a package with standardized entry points. Imports are sibling-module based (`from mainTango import ETL_TANGO`, `from util import getAMSTransaction`), so running from the project root matters.
- Dates are represented as `datetime.date` / `datetime.datetime`, and output filenames are built with `strftime('%Y%m%d')`.
- Most ETL tasks write directly to `./staggingArea/...` and `./output/reconciliation/...` relative to the current working directory. Preserve those path conventions when adding or debugging code.
- Several scripts use hard-coded SQL Server / ODBC connection strings (`util.py`, `ETL.py`, `reconciliation.py`, `Check_transaction_before_reconciliation.py`). Treat these as operational configuration rather than generic app settings.
- ETL functions commonly return a small status payload of the form `{"code": 200, "Status": "success", "message": ...}`. Match that shape when adding new pipeline steps.
- Source files are usually Excel-based and are consumed with `pandas.read_excel` and `to_excel`. Transformations often include data cleanup, type normalization, and deduplication in-place rather than through a formal schema layer.
- A lot of the logic intentionally prints detailed debug output instead of structured logging. When debugging a pipeline issue, inspect the console output first, then the generated staging files.

## Operational notes
- The pipeline depends on pre-existing source files and database access. Empty DataFrames, missing Excel files, and SQL connectivity problems are common failure modes in this repo.
- The reconciliation logic in `reconciliation.py` uses a multi-step match strategy: amount, transaction type, then time difference. Keep that ordering in mind when changing matching behavior.
- `mainOM.py` and `reconciliation.py` expect input columns and filenames to remain stable. Renaming columns or changing Excel schemas can break downstream logic even if the surrounding Python code still runs.
