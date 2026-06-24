# src_v2 Migration Workspace

This directory is the isolated workspace for the next-generation ART Q toolset.

## Purpose

- Preserve the stability of the production-ready [`src/`](../src/) tree
- Duplicate and evolve runtime modules safely in [`src_v2/`](./)
- Introduce shared cross-tool improvements before replacing current flows
- Build a unified Phase 6 UI system used consistently across all tools

## Initial Scope

The v2 workspace mirrors the top-level package layout of the current source tree:

- [`ART Q Control/`](./ART%20Q%20Control/)
- [`Archiver/`](./Archiver/)
- [`Assigner/`](./Assigner/)
- [`file_processing/`](./file_processing/)
- [`Merger/`](./Merger/)
- [`Reach Rate Calculator/`](./Reach%20Rate%20Calculator/)
- [`ui/`](./ui/)
- [`utils/`](./utils/)

## Migration Principles

1. Keep current production behavior untouched in [`src/`](../src/)
2. Prefer improving shared abstractions before editing individual tools
3. Centralize UI patterns in the v2 [`ui/`](./ui/) package
4. Preserve PyQt safety rules from [`AGENTS.md`](../AGENTS.md)
5. Maintain compatibility with path handling for [`ART Q Control/`](./ART%20Q%20Control/)

## First Implementation Targets

- V2 dispatcher bootstrap
- Shared automation runtime foundation
- Unified dialog and workflow shell
- Consistent theming, settings, accessibility, and progress feedback
- Tool adapters for Auto Sender, Case Reviewer, Companies Process, Assigner, Merger, Archiver, and Reach Rate Calculator

## Entry Point

Run [`main.py`](./main.py) to launch the isolated v2 application once the dispatcher and tool adapters are in place.