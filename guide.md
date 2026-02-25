# User Guide: Personal Knowledge Graph Engine

This guide explains the internal logic and workflows of the Personal Knowledge Graph Engine.

## Core Philosophy

1.  **Determinism**: The same input always produces the exact same graph structure.
2.  **Explicit Scoping**: Concepts do not automatically merge across units or subjects. "Entropy" in *Thermodynamics* is a different node from "Entropy" in *Information Theory*.
3.  **Provenance**: The graph knows exactly where every piece of information came from.

## The Ingestion Pipeline (`kg load`)

When you run `kg load`, the following steps occur sequentially:

### 1. PDF Processing & Text Cleaning
The system extracts text from your PDF. To ensure high-quality data, it applies cleaning heuristics:
-   **Page Numbers**: Lines containing only numbers are removed.
-   **Headers/Footers**: Lines that repeat identically across multiple pages are identified and stripped.
-   **Line Merging**: "Broken" lines (where a sentence halts in the middle) are merged back together.

### 2. Content Hashing
A SHA-256 hash is computed from the *cleaned* text. This hash is the fingerprint of your note.
-   **Identical Hash**: If you try to load the same file again, the system detects the hash match and **SKIPS** ingestion to save time.
-   **Changed Hash**: If you modified the PDF, the system detects the change, **REMOVES** the old nodes/edges associated with that file, and **REBUILDS** them from scratch.

### 3. Concept Extraction
Concepts are extracted using linguistic rules, not AI.
-   **Noun Phrases**: Detects capitalized terms (e.g., "Kinetic Energy", "Bernoulli Principle").
-   **Frequency Filter**: A term must appear at least **2 times** in the document to qualify as a concept.
-   **Normalization**: Terms are lowercased and whitespace-trimmed for ID generation.

### 4. Graph Construction
The graph is built with specific node types:

*   **Subject**: `subject::{name}`
*   **Unit**: `unit::{subject}::{name}`
*   **Note**: `note::{absolute_filepath}`
*   **Concept**: `concept::{subject}::{unit}::{term}`

**Edges** are created with a `source_note` attribute, ensuring that if a note is deleted, we know exactly which edges to remove.

## Data Persistence

The graph is saved to `knowledge_graph.json` in the current directory. This is a standard JSON file tracking all nodes and edges.

### JSON Structure
```json
{
  "nodes": {
    "concept::Physics::Thermodynamics::entropy": {
      "type": "concept",
      "term": "entropy"
    }
  },
  "edges": [
    {
      "source": "note::/abs/path/to/file.pdf",
      "target": "concept::Physics::Thermodynamics::entropy",
      "relation": "mentions",
      "source_note": "note::/abs/path/to/file.pdf"
    }
  ]
}
```

## Troubleshooting

-   **"No text extracted"**: Check if your PDF is a scanned image. This tool requires text-based PDFs.
-   **Concepts not appearing**: Ensure the term appears at least twice and is capitalized in the text (e.g., "The **G**radient **D**escent algorithm...").
