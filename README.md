# LimAuto

LimAuto is an experimental pipeline for generating technical books using a local LLM.
It orchestrates multiple agents (writers, proofreaders, code example generators, etc.)
through a graph defined in `BookLLM`.

## Prerequisites

- **Python 3.10+**
- **Ollama** – used to run the local LLM model. Install it from [https://ollama.ai](https://ollama.ai)
  and ensure the service is running (`ollama serve`) with a model available (e.g. `ollama pull llama3.1:8b`).
- Optional: create a virtual environment for the project.

## Installation

1. Clone this repository.
2. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Some dependencies are heavy and may require additional system libraries. If
   installation fails due to network restrictions, you can edit the requirements
   file to remove optional packages.

## Configuration

A sample configuration file is provided at `BookLLM/config.yaml`. It defines the
LLM model name, system options and cost tracking. You can modify this file or
pass a different YAML file when running the program.

Key options include:

- `model.name` – the Ollama model to use.
- `system.output_dir` – where generated files are saved.

## Running the book generator

Run the entry script with a topic and optional arguments:

```bash
python -m BookLLM.src.main "My Book Topic" \
  --config BookLLM/config.yaml \
  --audience beginners \
  --style professional \
  --pages 100 \
  --lang en
```

The generated book (Markdown), metadata and token metrics will be written to the
folder specified in the configuration (default: `book_output`).

## Running tests

The repository contains a small test suite. After installing the dependencies you
can run:

```bash
pytest
```

## Repository layout

- `BookLLM/` – source code and configuration
- `tests/` – additional tests used during development
- `requirements.txt` – Python dependencies

Feel free to explore the source code for more details on how each agent works.


## License
See [LICENSE](LICENSE) for license details.

