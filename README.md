# CPSC 362 Project

## Running

Requires Python 3.10 or higher. Optionally, these dependencies are required:

- Pyright for autocompletion/LSP
- Black for Python formatting
- Prettier for HTML/CSS/JS formatting

A virtual environment is recommended. If you're not already using the Nix
shell, then you'll need to create one by running:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then, install the dependencies:

```bash
pip3 install -r requirements.txt
```

Then, run the server:

```bash
python3 -m server
```
