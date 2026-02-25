#!/usr/bin/env python3
"""
Personal Knowledge Graph Engine CLI.
"""

import sys
import argparse
import os
from collections import defaultdict

from pdf_extractor import PDFExtractor
from concept_extractor import ConceptExtractor
from graph_manager import GraphManager
from persistence import GraphPersistence


def main():
    parser = argparse.ArgumentParser(description="Personal Knowledge Graph Engine")
    sub = parser.add_subparsers(dest="command")

    # kg load
    load = sub.add_parser("load", help="Load a PDF into the knowledge graph")
    load.add_argument("--subject", required=True)
    load.add_argument("--unit", required=True)
    load.add_argument("pdf_file")

    # kg concepts
    concepts = sub.add_parser("concepts", help="List concepts for a subject/unit")
    concepts.add_argument("--subject", required=True)
    concepts.add_argument("--unit", required=True)

    # kg related
    related = sub.add_parser("related", help="Find related concepts")
    related.add_argument("--subject", required=True)
    related.add_argument("--unit", required=True)
    related.add_argument("concept")

    # kg status
    status = sub.add_parser("status", help="Show knowledge graph summary")

    args = parser.parse_args()

    if args.command == "load":
        cmd_load(args.subject, args.unit, args.pdf_file)
    elif args.command == "concepts":
        cmd_concepts(args.subject, args.unit)
    elif args.command == "related":
        cmd_related(args.subject, args.unit, args.concept)
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()
        sys.exit(1)


def cmd_load(subject: str, unit: str, pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    extractor = PDFExtractor(pdf_path)
    text, content_hash = extractor.extract_text()

    concept_extractor = ConceptExtractor(min_frequency=2)
    concepts = concept_extractor.extract_concepts(text)

    persistence = GraphPersistence()
    graph = persistence.load()

    manager = GraphManager(graph)
    result = manager.load_note(
        pdf_path=pdf_path,
        subject=subject,
        unit=unit,
        content_hash=content_hash,
        cleaned_text=text,
        concepts=concepts
    )

    persistence.save(graph)

    print("=" * 40)
    print(f"STATUS:   {result['action'].upper()}")
    print(f"CONCEPTS: {result['concepts_count']}")
    print(f"EDGES:    {result['edges_count']}")
    print("=" * 40)


def cmd_concepts(subject: str, unit: str):
    persistence = GraphPersistence()
    graph = persistence.load()

    unit_id = f"unit::{subject}::{unit}"

    if not graph.has_node(unit_id):
        print("No such unit.")
        return

    concepts = []
    for node_id, data in graph.nodes(data=True):
        if data.get("type") == "concept" and graph.has_edge(node_id, unit_id):
            concepts.append(data)

    concepts.sort(key=lambda x: x["normalized"])

    print(f"[Subject: {subject}]")
    print(f"[Unit: {unit}]")
    print("-" * 40)

    for i, c in enumerate(concepts, 1):
        print(f"{i}. {c['term']}")
        print(f"   normalized : {c['normalized']}")
        aliases = c.get("aliases", [])
        print(f"   aliases    : {', '.join(aliases) if aliases else 'none'}")
        print()

    print("-" * 40)
    print(f"Total concepts: {len(concepts)}")


def cmd_related(subject: str, unit: str, concept_term: str):
    persistence = GraphPersistence()
    graph = persistence.load()

    normalized = concept_term.lower().strip()
    concept_id = f"concept::{subject}::{unit}::{normalized}"

    if not graph.has_node(concept_id):
        print(f"Concept not found: {concept_term}")
        return

    notes = [
        n for n in graph.predecessors(concept_id)
        if graph.nodes[n].get("type") == "note"
    ]

    related_counts = {}

    for note in notes:
        for target in graph.successors(note):
            if graph.nodes[target].get("type") == "concept" and target != concept_id:
                related_counts[target] = related_counts.get(target, 0) + 1

    if not related_counts:
        print("No related concepts found.")
        return

    print(f"Related concepts for: {concept_term}")
    print(f"[Subject: {subject} / Unit: {unit}]")
    print("-" * 40)

    for i, (cid, count) in enumerate(
        sorted(related_counts.items(), key=lambda x: x[1], reverse=True), 1
    ):
        print(f"{i}. {graph.nodes[cid]['term']} (shared notes: {count})")

    print("-" * 40)


def cmd_status():
    persistence = GraphPersistence()
    graph = persistence.load()

    counts = defaultdict(int)
    unit_concept_counts = defaultdict(int)

    for node_id, data in graph.nodes(data=True):
        node_type = data.get("type")
        if node_type:
            counts[node_type] += 1

        if node_type == "concept":
            for target in graph.successors(node_id):
                if graph.nodes[target].get("type") == "unit":
                    unit_concept_counts[target] += 1

    print("Knowledge Graph Status")
    print("-" * 30)
    print(f"Subjects : {counts.get('subject', 0)}")
    print(f"Units    : {counts.get('unit', 0)}")
    print(f"Notes    : {counts.get('note', 0)}")
    print(f"Concepts : {counts.get('concept', 0)}")
    print(f"Edges    : {graph.number_of_edges()}")

    if unit_concept_counts:
        print("\nConcepts per unit:")
        for unit_id, cnt in sorted(unit_concept_counts.items(), key=lambda x: x[1], reverse=True):
            print(f" - {unit_id.replace('unit::', '')}: {cnt}")

    print("-" * 30)


if __name__ == "__main__":
    main()