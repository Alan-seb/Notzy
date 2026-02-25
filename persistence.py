"""
Graph persistence to/from JSON.
"""
import json
import os
from typing import Dict, Any
import networkx as nx


class GraphPersistence:
    """Handles loading and saving the knowledge graph to JSON."""
    
    def __init__(self, filepath: str = "knowledge_graph.json"):
        self.filepath = filepath
    
    def load(self) -> nx.DiGraph:
        """Load graph from JSON file. Returns empty graph if file doesn't exist."""
        if not os.path.exists(self.filepath):
            return nx.DiGraph()
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = nx.DiGraph() 
        
        # Add nodes with attributes
        for node_id, attrs in data.get('nodes', {}).items():
            graph.add_node(node_id, **attrs)

        # Add edges with attributes
        for edge in data.get('edges', []):
            source = edge['source']
            target = edge['target']
            attrs = {k: v for k, v in edge.items() if k not in ['source', 'target']}
            graph.add_edge(source, target, **attrs)
        
        return graph
    
    def save(self, graph: nx.DiGraph) -> None:
        """Save graph to JSON file."""
        data: Dict[str, Any] = {
            'nodes': {},
            'edges': []
        }
        
        # Serialize nodes
        for node_id in graph.nodes():
            data['nodes'][node_id] = dict(graph.nodes[node_id])
        
        # Serialize edges
        for source, target in graph.edges():
            edge_data = {'source': source, 'target': target}
            edge_data.update(graph.edges[source, target])
            data['edges'].append(edge_data)
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

