# Scripts

These scripts are used by agents for specific commands and/or skills. 

For example:

- `/sync` command will invoke `sync_context.py`
- `run-python-safely` will direct an agent to run their scratch code with `run_python_safely.py` script

## Script tests

Most scripts have a complementing test file (`run_python_safely.py`, `test_run_python_safely.py`).

Run all script tests (with coverage):

```sh
uv run pytest --cov .claude/scripts/ .claude/scripts/
```