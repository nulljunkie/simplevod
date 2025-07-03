Setup the python environemnt

```bash
python -m venv .venv
source .venv/bin/activate
pip install requirements-dev.txt
```

Run the tests

```bash
python -m pytest tests -v
```

Run the Service

```bash
python main.py
```
