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

Nine unit tests passed against the local implementation; the published files have not been independently re-run from a GitHub checkout on Python 3.13.5 under Linux. The tests cover directory discovery, duplicate detection, JSON output, invalid UTF-8, file-size limits, symlink exclusion, and non-destructive reads. Further edge-case review remains.

## Development report — afternoon, November 4, 2026

The afternoon review found three problems: an explicitly supplied symlink was followed, file reads were not bounded if a file grew after the size check, and directory traversal errors could be silently skipped. Explicit symlink inputs are now rejected, reads stop after 2 MiB plus one byte, and traversal failures produce an error.

Nine additional tests passed locally on Python 3.13 under Linux. They cover symlinks, nested discovery, size boundaries, duplicate normalization, traversal errors, JSON output, and unchanged source bytes. The full repository test suite and an installed-wheel check were not run in this review because the local environment could not resolve github.com for a checkout. The updated source and tests were committed through the GitHub integration.

Known limitations: token counts are estimates; paragraph matching is exact after normalization, not semantic. Paths in reports may expose sensitive directory names. A concurrent file replacement during scanning is not fully protected against, and the tool does not determine which instructions take precedence.
