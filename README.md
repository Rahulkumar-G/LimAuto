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

### Option 1: Local Development Setup

1. Clone this repository.
2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:

   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. Start the development environment:

   ```bash
   # Start both backend and frontend
   python start_dev.py
   
   # Or start them separately:
   python start_backend.py  # Backend on http://localhost:8000
   python start_frontend.py # Frontend on http://localhost:3000
   ```

### Option 2: Docker Setup (Recommended)

1. Install Docker and Docker Compose
2. Clone this repository
3. Choose your environment:

   ```bash
   # Development environment with live reload
   ./docker-start.sh dev
   
   # Production environment
   ./docker-start.sh prod
   
   # Stop all services
   ./docker-start.sh stop
   
   # Clean up Docker resources
   ./docker-start.sh clean
   ```

### Quick Start

```bash
# 1. Start the backend API
python start_backend.py

# 2. In another terminal, start the frontend
python start_frontend.py

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Health Check: http://localhost:8000/health
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
python start_backend.py
# or
python -m BookLLM.src.api
```

Generate a book via API:

```bash
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" \
  -d '{"topic": "My Book Topic"}'
```

### API Endpoints

- `GET /health` - Health check
- `GET /api/agents` - List available agents
- `GET /api/metrics` - Get token usage metrics
- `GET /api/agent-starts` - Get agent start times
- `POST /generate` - Generate a book
- `POST /api/dispatch` - Send prompt to specific agent
- `GET /events/agent-status` - Real-time status updates (SSE)

### Frontend UI

The React frontend provides a user-friendly interface for:
- Book generation with custom parameters
- Real-time progress monitoring
- Agent status tracking
- Metrics visualization
- Export management

Access it at http://localhost:3000 after starting both backend and frontend services.

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

