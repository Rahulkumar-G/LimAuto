# LangGraphBook

LangGraphBook: An LLM-driven orchestration framework for building AI-powered books.
It orchestrates multiple agents (writers, proofreaders, code example generators, etc.)
through a graph defined in `BookLLM`.

## Prerequisites

- **Python 3.10+**
- **Ollama** – used to run the local LLM model. Install it from [https://ollama.ai](https://ollama.ai)
  and ensure the service is running (`ollama serve`) with a model available (e.g. `ollama pull llama3.1:8b`).
- Optional: create a virtual environment for the project.

## Installation

1. Clone this repository.
2. Install the package and dependencies:

   ```bash
   pip install .
   ```

3. Alternatively build a Docker image:

   ```bash
   docker build -t langgraphbook .
   docker run -p 8000:8000 langgraphbook
   ```

## Configuration

A sample configuration file is provided at `BookLLM/config.yaml`. It defines the
LLM model name, system options and cost tracking. You can modify this file or
pass a different YAML file when running the program.

Key options include:

- `model.name` – the Ollama model to use.
- `system.output_dir` – where generated files are saved.

## Usage

### Command Line Interface

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

### HTTP API

Start the API server:

```bash
python -m BookLLM.src.api
```

Generate a book via API:

```bash
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" \
  -d '{"topic": "My Book Topic"}'
```

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

## Documentation
Comprehensive documentation lives in the [docs/](docs/) directory. If you find an issue, please report it on the [issue tracker](https://github.com/yourorg/langgraphbook/issues).

## Contributing
We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on opening issues and submitting pull requests.

## License
See [LICENSE](LICENSE) for license details.

