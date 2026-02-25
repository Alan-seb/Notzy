# Personal Knowledge Graph Engine
‼️STATUS:ONGOING
A strictly deterministic, CLI-based tool for ingesting PDF notes into a structured knowledge graph.

## Features

- **Deterministic Ingestion**: No AI, no embeddings, no "smart" guessing. Consistently reproducible results.
- **Strict Scoping**: Concepts are uniquely scoped to `{subject}::{unit}::{term}`.
- **Idempotency**: Smart handling of file updates. Re-processing the same file skips execution; modifying the file rebuilds only that note's subgraph.
- **Provenance**: Every node and edge is traceable to its source.

## Installation

1. **Clone the repository** (or download files).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The tool exposes a single command: `kg load`.

```bash
python3 kg.py load --subject "SUBJECT_NAME" --unit "UNIT_NAME" path/to/file.pdf
```

### Example

```bash
python3 kg.py load --subject "Physics" --unit "Thermodynamics" ./lecture_notes.pdf
```

### Output

The tool provides a clear report of actions taken:

```text
Processing: ./lecture_notes.pdf
Subject: Physics
Unit: Thermodynamics
----------------------------------------
Extracting text... Done.
Extracting concepts... Found 15 candidates.
Updating graph... Done.
========================================
EXECUTION REPORT
========================================
Status:         LOADED
Subject:        Physics
Unit:           Thermodynamics
Concepts:       15 added/linked
Edges:          15 created
----------------------------------------
```
