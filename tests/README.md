# Testing Guide

This project uses pytest as a testing framework. Here are the guidelines for running the tests。

## Install dependencies

Before running tests, make sure all development dependencies are installed：

```bash
pip install -r requirements.txt
```

## Run tests

### Run all tests

```bash
pytest
```

### Run a specific test file

```bash
pytest tests/integration/test_api_tasks.py
```

### Run a specific test function

```bash
pytest tests/unit/test_utils.py::test_safe_get_nested_and_default
```

### Generate coverage report

```bash
coverage run -m pytest
coverage report
coverage html  # generate HTML Report
```

## Test file structure

```
tests/
├── __init__.py
├── conftest.py              # shared fixtures（API/CLI/sample data）
├── fixtures/                # Close to real sample data (search/user/evaluate/Task configuration）
│   ├── config.sample.json
│   ├── ratings.json
│   ├── search_results.json
│   ├── state.sample.json
│   ├── user_head.json
│   └── user_items.json
├── integration/             # Critical link integration testing（API/CLI/parser）
│   ├── test_api_tasks.py
│   ├── test_cli_spider.py
│   └── test_pipeline_parse.py
└── unit/                    # Core pure function unit testing
    ├── test_domain_task.py
    └── test_utils.py
```

## Write new tests

1. Add new tests in `tests/integration/` or `tests/unit/`
2. The file name starts with `test_` Starting with, the function name starts with `test_` beginning
3. Tests are executed synchronously (do not rely on pytest-asyncio）
4. external dependencies（Playwright/AI/notify/network) unification mock
5. use `tests/fixtures/` sample data to avoid relying on real networks

## Things to note

1. The goal is to be runable offline and reproducible stably.
2. Integration tests give priority to covering real running links（API、CLI、parser）
3. If you need to add real scene examples, please add them to `tests/fixtures/`
