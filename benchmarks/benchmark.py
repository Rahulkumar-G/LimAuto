import time
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pandas as pd
from BookLLM.src.models.state import BookState
from BookLLM.src.models.config import SystemConfig, ModelConfig, CostConfig, TokenMetrics
from BookLLM.src.agents.content.outline import OutlineAgent
from BookLLM.src.agents.content.writer import WriterAgent
from BookLLM.src.agents.content.chapter import ChapterWriterAgent
from BookLLM.src.agents.enhancement.glossary import GlossaryAgent
from BookLLM.src.agents.enhancement.code import CodeSampleAgent


class DummyLLM:
    """Simplified LLM stub used for benchmarks."""

    def __init__(self):
        self.system_config = SystemConfig(output_dir=Path("benchmark_output"))
        self.model_config = ModelConfig()
        self.cost_config = CostConfig()
        self.metrics = TokenMetrics()

    def call_llm(self, prompt: str, json_mode: bool = False, **kwargs):
        if "book outline" in prompt:
            return '["Intro","Chapter 1"]', {}
        if "Extract and define technical terms" in prompt:
            return '{"term":"definition"}', {}
        if "Write a comprehensive chapter" in prompt:
            return "This chapter includes code snippets", {}
        if "Create practical code examples" in prompt:
            return "```python\nprint('example')\n```", {}
        return "text", {}

    async def acall_llm(self, prompt: str, json_mode: bool = False, **kwargs):
        return self.call_llm(prompt, json_mode=json_mode, **kwargs)


def measure_agent(agent_cls, state, input_size, llm):
    """Measure execution time of an agent."""
    agent = agent_cls(llm)
    start = time.perf_counter()
    agent.process(state)
    run_time = time.perf_counter() - start
    return {
        "agent_name": agent_cls.__name__,
        "input_size": input_size,
        "run_time_seconds": run_time,
    }


def main():
    llm = DummyLLM()
    results = []

    # OutlineAgent with 500-word topic
    topic = "word " * 500
    state = BookState(topic=topic.strip())
    results.append(measure_agent(OutlineAgent, state, 500, llm))

    # WriterAgent on 5-section outline
    outline = [f"Section {i}" for i in range(1, 6)]
    state = BookState(topic="Benchmark", outline=outline, chapters=outline.copy())
    results.append(measure_agent(WriterAgent, state, len(outline), llm))

    # ChapterWriterAgent on 5 chapters
    state = BookState(topic="Benchmark", chapters=outline.copy())
    results.append(measure_agent(ChapterWriterAgent, state, len(outline), llm))

    # GlossaryAgent on generated chapter map
    chapter_map = {c: "Content about example" for c in outline}
    state = BookState(topic="Benchmark", chapter_map=chapter_map, chapters=outline.copy())
    input_words = sum(len(v.split()) for v in chapter_map.values())
    results.append(measure_agent(GlossaryAgent, state, input_words, llm))

    # CodeSampleAgent on single chapter
    chapter_map = {"Intro": "This chapter includes code snippets"}
    state = BookState(topic="Benchmark", chapter_map=chapter_map, chapters=["Intro"])
    results.append(measure_agent(CodeSampleAgent, state, 1, llm))

    df = pd.DataFrame(results)
    output_dir = Path("benchmarks")
    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "results.csv", index=False)
    print(df)

    # Optimization suggestions (example)
    if df[df.agent_name == "WriterAgent"].run_time_seconds.iloc[0] > 30:
        # If WriterAgent is slow, lower max_tokens or parallelize chapters
        pass


if __name__ == "__main__":
    main()
