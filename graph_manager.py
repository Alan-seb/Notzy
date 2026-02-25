"""
Knowledge graph management with NetworkX.
"""

from typing import List, Dict, Any, Optional
import networkx as nx
import os


class GraphManager:
    """Manages the knowledge graph structure and operations."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def load_note(
        self,
        pdf_path: str,
        subject: str,
        unit: str,
        content_hash: str,
        cleaned_text: str,
        concepts: List
    ) -> Dict[str, Any]:

        note_id = self._create_note_id(pdf_path)
        existing_hash = self._get_note_hash(note_id)

        if existing_hash == content_hash:
            return {
                "action": "skipped",
                "note_id": note_id,
                "concepts_count": 0,
                "edges_count": 0
            }

        if existing_hash is not None:
            self._remove_note_contribution(note_id)
            action = "rebuilt"
        else:
            action = "loaded"

        subject_id = self._create_subject_id(subject)
        self._ensure_subject_node(subject_id, subject)

        unit_id = self._create_unit_id(subject, unit)
        self._ensure_unit_node(unit_id, subject_id, unit)

        self._create_note_node(note_id, unit_id, pdf_path, content_hash, cleaned_text)

        edges_count = 0
        for term, normalized in concepts:
            concept_id = self._create_concept_id(subject, unit, normalized)
            self._ensure_concept_node(concept_id, unit_id, term, normalized)
            self._create_note_concept_edge(note_id, concept_id)
            edges_count += 1

        return {
            "action": action,
            "note_id": note_id,
            "concepts_count": len(concepts),
            "edges_count": edges_count
        }

    # ───────────────────────── IDs ─────────────────────────

    def _create_subject_id(self, subject: str) -> str:
        return f"subject::{subject}"

    def _create_unit_id(self, subject: str, unit: str) -> str:
        return f"unit::{subject}::{unit}"

    def _create_note_id(self, pdf_path: str) -> str:
        return f"note::{os.path.abspath(pdf_path)}"

    def _create_concept_id(self, subject: str, unit: str, normalized: str) -> str:
        return f"concept::{subject}::{unit}::{normalized}"

    # ───────────────────────── Nodes ─────────────────────────

    def _ensure_subject_node(self, subject_id: str, subject: str) -> None:
        if not self.graph.has_node(subject_id):
            self.graph.add_node(subject_id, type="subject", name=subject)

    def _ensure_unit_node(self, unit_id: str, subject_id: str, unit: str) -> None:
        if not self.graph.has_node(unit_id):
            self.graph.add_node(unit_id, type="unit", name=unit)
            self.graph.add_edge(
                unit_id,
                subject_id,
                relation="belongs_to",
                source_note="system"
            )

    def _create_note_node(
        self,
        note_id: str,
        unit_id: str,
        pdf_path: str,
        content_hash: str,
        cleaned_text: str
    ) -> None:
        self.graph.add_node(
            note_id,
            type="note",
            pdf_path=os.path.abspath(pdf_path),
            content_hash=content_hash,
            text=cleaned_text
        )
        self.graph.add_edge(
            note_id,
            unit_id,
            relation="belongs_to",
            source_note="system"
        )

    def _ensure_concept_node(
        self,
        concept_id: str,
        unit_id: str,
        term: str,
        normalized: str
    ) -> None:
        if self.graph.has_node(concept_id):
            node = self.graph.nodes[concept_id]
            aliases = set(node.get("aliases", []))
            if term != node["term"]:
                aliases.add(term)
                node["aliases"] = sorted(aliases)
            return

        self.graph.add_node(
            concept_id,
            type="concept",
            term=term,
            normalized=normalized,
            aliases=[]
        )
        self.graph.add_edge(
            concept_id,
            unit_id,
            relation="scoped_to",
            source_note="system"
        )

    def _create_note_concept_edge(self, note_id: str, concept_id: str) -> None:
        if not self.graph.has_edge(note_id, concept_id):
            self.graph.add_edge(
                note_id,
                concept_id,
                relation="mentions",
                source_note=note_id
            )

    # ───────────────────────── Rebuild helpers ─────────────────────────

    def _get_note_hash(self, note_id: str) -> Optional[str]:
        if self.graph.has_node(note_id):
            return self.graph.nodes[note_id].get("content_hash")
        return None

    def _remove_note_contribution(self, note_id: str) -> None:
        if not self.graph.has_node(note_id):
            return

        concepts = [
            t for t in self.graph.successors(note_id)
            if self.graph.nodes[t].get("type") == "concept"
        ]

        self.graph.remove_node(note_id)

        for cid in concepts:
            if not self._concept_has_other_sources(cid, note_id):
                self.graph.remove_node(cid)

    def _concept_has_other_sources(self, concept_id: str, excluding_note: str) -> bool:
        for pred in self.graph.predecessors(concept_id):
            if self.graph.nodes[pred].get("type") == "note":
                for _, _, data in self.graph.edges(pred, concept_id, data=True):
                    if data.get("source_note") != excluding_note:
                        return True
        return False
