import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class ChapterWriterAgent(BaseAgent):
    """Handles chapter content generation"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Execute chapter writing based on configuration"""
        if self.llm.system_config.parallel_agents:
            return self._write_chapters_parallel(state)
        else:
            return self._write_chapters_sequential(state)

    def _write_chapters_sequential(self, state: BookState) -> BookState:
        """Write chapters sequentially"""
        total = len(state.chapters)
        with tqdm(total=total, desc="Chapters", unit="chapter") as pbar:
            for i, title in enumerate(state.chapters):
                self.logger.info(
                    f"Writing chapter {i + 1}/{total}: {title}"
                )
                content = self._write_single_chapter(title, state, i)
                state.chapter_map[title] = content
                pbar.update(1)
        return state

    def _write_chapters_parallel(self, state: BookState) -> BookState:
        """Write chapters in parallel"""
        with ThreadPoolExecutor(
            max_workers=self.llm.system_config.max_workers
        ) as executor:
            future_to_chapter = {
                executor.submit(self._write_single_chapter, title, state, i): title
                for i, title in enumerate(state.chapters)
            }
            total = len(state.chapters)
            with tqdm(total=total, desc="Chapters", unit="chapter") as pbar:
                for future in as_completed(future_to_chapter):
                    title = future_to_chapter[future]
                    try:
                        content = future.result()
                        state.chapter_map[title] = content
                        self.logger.info(f"✅ Completed chapter: {title}")
                    except Exception as e:
                        error_msg = f"Failed to write chapter '{title}': {e}"
                        self.logger.error(error_msg)
                        state.errors.append(error_msg)
                    pbar.update(1)

        return state

    def _write_single_chapter(
        self, title: str, state: BookState, chapter_index: int
    ) -> str:
        """Generate content for a single chapter"""
        previous_chapters = self._get_previous_chapters_context(state, chapter_index)
        prompt = self._build_chapter_prompt(
            title, state, chapter_index, previous_chapters
        )
        content, _ = self.llm.call_llm(prompt)
        return self._post_process_chapter(content, state, title)

    def _build_chapter_prompt(
        self, title: str, state: BookState, chapter_index: int, previous_chapters: str
    ) -> str:
        """Build detailed chapter generation prompt"""
        return f"""
        Write a comprehensive chapter titled "{title}" for a book on "{state.topic}".
        
        Context:
        - Target audience: {state.target_audience}
        - Book style: {state.book_style}
        - Chapter {chapter_index + 1} of {len(state.chapters)}
        - Previous chapters: {previous_chapters}
        
        Required Chapter Structure:
        1. Chapter Overview (100-150 words)
        2. Introduction (300-400 words)
        3. Main Content (2000-2500 words)
        4. Practical Examples (400-500 words)
        5. Chapter Summary (200-300 words)
        6. Exercises and Projects
        7. Further Reading
        
        Use proper Markdown formatting.
        Target Length: 3000-4000 words total
        """

    def _post_process_chapter(self, content: str, state: BookState, title: str) -> str:
        """Post-process chapter content"""
        try:
            # Update statistics
            self._update_chapter_statistics(content, state)

            # Add navigation
            nav_header = self._create_navigation_header(title, state)

            # Add reading time
            reading_info = self._create_reading_info(content)

            return f"{nav_header}\n{reading_info}\n{content}"

        except Exception as e:
            self.logger.error(f"Error in post-processing chapter {title}: {e}")
            return content

    def _get_previous_chapters_context(
        self, state: BookState, current_index: int
    ) -> str:
        """Get context from previous chapters"""
        return "\n".join(
            f"Chapter {i+1}: {ch_title} - {state.chapter_summaries.get(ch_title, 'No summary')}"
            for i, ch_title in enumerate(state.chapters[:current_index])
        )

    def _update_chapter_statistics(self, content: str, state: BookState) -> None:
        """Update basic statistics for the chapter content."""
        image_pattern = re.compile(r"!\[[^\]]*\]\([^)]*\)")
        link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\([^)]*\)")

        images = len(image_pattern.findall(content))
        links = len(link_pattern.findall(content))
        tables = len(re.findall(r"\n\|", content))
        code_blocks = content.count("```") // 2
        examples = len(re.findall(r"\bexample\b", content, re.IGNORECASE))

        state.total_images += images
        state.total_references += links
        state.total_tables += tables
        state.total_code_blocks += code_blocks
        state.total_examples += examples

    def _create_navigation_header(self, title: str, state: BookState) -> str:
        """Create simple navigation links between chapters."""
        index = state.chapters.index(title)
        prev_chapter = state.chapters[index - 1] if index > 0 else None
        next_chapter = (
            state.chapters[index + 1] if index + 1 < len(state.chapters) else None
        )

        parts = []
        if prev_chapter:
            parts.append(f"[<< {prev_chapter}](#{prev_chapter.replace(' ', '-')})")
        parts.append(f"**{title}**")
        if next_chapter:
            parts.append(f"[{next_chapter} >>](#{next_chapter.replace(' ', '-')})")

        return " | ".join(parts)

    def _create_reading_info(self, content: str) -> str:
        """Return an estimated reading time string for the chapter."""
        words = len(content.split())
        minutes = max(1, int(words / 200))
        return f"_Estimated reading time: {minutes} minute(s)_"
