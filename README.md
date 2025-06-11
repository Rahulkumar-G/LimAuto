# LangGraphBook

LangGraphBook: An LLM-driven orchestration framework for building AI-powered books.
It orchestrates multiple agents (writers, proofreaders, code example generators, etc.)
through a graph defined in `BookLLM`.

## Prerequisites

- **Python 3.10+**
- **Ollama** – used to run the local LLM model. Install it from [https://ollama.ai](https://ollama.ai)
  and ensure the service is running (`ollama serve`) with a model available (e.g. `ollama pull llama3.1:8b`).
- Optional: create a virtual environment for the project.
- **Pandoc** and **xelatex** – used for high quality PDF output. If they are not installed the program falls back to **fpdf2** for basic PDF generation.

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
LLM provider, model name, system options and cost tracking. You can modify this
file or pass a different YAML file when running the program.

Key options include:

- `model.provider` – either `ollama` for local models or `openai` for the
  OpenAI API.
- `model.name` – the model name (e.g. `llama3.1:8b`, `gpt-4o`).
- `system.output_dir` – where generated files are saved.
- `system.agent_sequence` – list of agents to run in order.

## Usage

### Command Line Interface

Run the entry script with a topic and optional arguments:

```bash
python -m BookLLM.src.main "My Book Topic" \
  --config BookLLM/config.yaml \
  --audience beginners \
  --style professional \
  --pages 100 \
  --lang en \
  --pdf
```

The generated book (Markdown), metadata and token metrics will be written to the
folder specified in the configuration (default: `book_output`). If `--pdf` is
specified a PDF version will also be generated. The exporter will use Pandoc and
`xelatex` when available, otherwise it falls back to the lightweight `fpdf2`
library. Before exporting, a style guide enforcer normalizes heading levels and
emphasis in the generated Markdown.

During generation you will see a **step tracker** showing the current phase
(e.g. `Step 1/3: Scaffolding`) and a progress bar for chapter creation. The
process is complete when the log prints `✅ Book generation completed!` along
with the output directory path.

### HTTP API

Start the API server:

```bash
python -m BookLLM.src.api
```

To serve both the backend API and a static UI in one step run:

```bash
python run_combined.py
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
- `frontend/` – React components and UI code

Feel free to explore the source code for more details on how each agent works.

Recent updates introduced automated generation of front and back matter
including acknowledgments, about-the-author bios, a standardized glossary,
bibliography, and index. Citation style now defaults to APA and glossary terms
are automatically cross-referenced in the index.

## Metrics dashboard

The `frontend/` directory contains a small React component `MetricsPage.tsx`.
It visualizes success vs. failure as a pie chart and shows a 24‑hour trendline
with stacked areas using Recharts.

`AgentStatusPanel.tsx` retrieves `/api/agent-starts` so you can view when each
agent began executing.

## Documentation
Comprehensive documentation lives in the [docs/](docs/) directory. If you find an issue, please report it on the [issue tracker](https://github.com/yourorg/langgraphbook/issues).

## Contributing
We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on opening issues and submitting pull requests.

## License
See [LICENSE](LICENSE) for license details.

## Dashboard Integration

An example `MetricsChartSection` component is provided in
`dashboard/src/components/MetricsChartSection.tsx`. Embed it inside your
dashboard grid layout to display latency and token usage charts.

```jsx
import './dashboard/src/components/MetricsChartSection'
import MetricsChartSection

export default function DashboardGrid() {
  return (
    <div className="dashboard-grid">
      {/* other widgets */}
      <MetricsChartSection />
    </div>
  );
}
```

`MetricsChartSection` automatically requests data from `/api/metrics` but shows
its built-in mock dataset when the request fails.

