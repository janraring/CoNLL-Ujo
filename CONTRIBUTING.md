# Contributing to CoNLL-Ujo

Thanks for helping build CoNLL-Ujo! This document covers the basics of how we work together.

## Workflow

1. **Start from an issue.** Before writing code, check if there's an open issue for the work. If not, open one describing what you want to do — this gives us a place to discuss scope and approach before code gets written.
2. **Create a branch** for your work (see naming convention below).
3. **Open a pull request** against `main` when your branch is ready for review. Link it to the relevant issue (e.g. `Closes #12` in the PR description).
4. **Wait for review and approval.** `main` is protected — all changes go through a PR with at least one approval before merging. Direct pushes to `main` aren't possible.
5. **Merge** once approved.

## Branch naming

Branches follow the pattern:

```
<type>/<short-description>
```

or, tied to an issue:

```
<type>/<issue-number>-<short-description>
```

**Common type prefixes:**

| Prefix | Use for |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `docs/` | Documentation-only changes |
| `refactor/` | Restructuring without behavior change |
| `test/` | Adding or fixing tests |
| `chore/` | Maintenance (dependencies, tooling, CI config) |

**Examples:**

```
feature/12-empty-node-support
fix/34-mwt-misc-merge
docs/readme-contributing
```

## A note on CoNLL-Ujo's core design philosophy

CoNLL-Ujo is built around a **clear separation between creation and validation**. The data model deliberately does *not* enforce CoNLL-U compliance by default — fields can be left unset, and no validation runs on read or write. This is intentional: it reflects the reality that treebank data can be messy and incomplete while it's being built. Compliance checking is a separate, explicit step.

## Code style

- Python, typed, src-layout.
- Format/lint with Ruff; type-check with Pyright.
- (Add test-running instructions here once the test setup is finalized.)

## Questions

If anything about the workflow or design is unclear, open an issue or ask directly — better to check than to guess.
