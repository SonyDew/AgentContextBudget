# AgentContextBudget

**Status: In Development** — SonyDev GitHub Marathon, Day 9 (November 4, 2026).

A local, read-only Python CLI that reports byte counts, approximate token counts, and repeated paragraphs across agent instruction files.

## Install and run

Requires Python 3.10 or later. No runtime dependencies.

```sh
python -m pip install .
agent-context-budget .
agent-context-budget . --json
python -m agent_context_budget . --json
```

The scanner recognizes `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `copilot-instructions.md` recursively. It skips symlinked files and directories, `.git`, `node_modules`, virtual environments, and Python cache directories. Individual files larger than 2 MiB are rejected.

Duplicate paragraphs are compared across different files after whitespace and case normalization. Paragraphs shorter than 40 normalized characters are ignored. Only SHA-256 prefixes and relative paths appear in duplicate reports; paragraph contents are not printed. Filenames may themselves contain sensitive information.

Token counts use `ceil(character_count / 4)` for each file. This is a rough size indicator, not a model tokenizer or a context-window measurement. Duplicate detection does not resolve inheritance, precedence, or semantic similarity.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Development report — morning, November 4, 2026

The initial CLI and nine unit tests were implemented and passed locally on Python 3.11 under Linux. The tests cover directory discovery, duplicate detection, JSON output, invalid UTF-8, file-size limits, symlink exclusion, and non-destructive reads. Further edge-case review remains.
