"""
Origin DevBridge - Mermaid Compiler & AST Layer
================================================
Compiles spatial DiagramNodes and positional coordinates into 
valid Mermaid.js flowchart syntax.
"""

import re
from typing import List
from dataclasses import dataclass

try:
    from .ocr_pipeline import DiagramNode
except ImportError:
    # Allows running directly as a standalone script
    from ocr_pipeline import DiagramNode


@dataclass
class DiagramEdge:
    source_id: str
    target_id: str
    label: str = ""
    arrow_type: str = "-->"


class MermaidCompiler:
    def __init__(self, direction: str = "LR"):
        """
        direction: 'LR' (Left-to-Right) or 'TD' (Top-to-Bottom)
        """
        normalized_direction = direction.upper()
        if normalized_direction not in {"LR", "TD"}:
            raise ValueError(
                f"Unsupported Mermaid flowchart direction '{direction}'. Use 'LR' or 'TD'."
            )
        self.direction = normalized_direction

    def build_edges_from_spatial_layout(self, nodes: List[DiagramNode]) -> List[DiagramEdge]:
        """
        Infers connections based on horizontal/vertical coordinates.
        Connects sequential nodes left-to-right (or top-to-bottom).
        """
        if len(nodes) < 2:
            return []

        if self.direction == "LR":
            # Left-to-right: primary X, tie-break Y
            sorted_nodes = sorted(nodes, key=lambda n: (n.centroid[0], n.centroid[1]))
        else:
            # Top-to-bottom: primary Y, tie-break X
            sorted_nodes = sorted(nodes, key=lambda n: (n.centroid[1], n.centroid[0]))

        edges: List[DiagramEdge] = []
        for i in range(len(sorted_nodes) - 1):
            src = sorted_nodes[i]
            dst = sorted_nodes[i + 1]
            edges.append(DiagramEdge(source_id=src.id, target_id=dst.id))

        return edges

    def compile(self, nodes: List[DiagramNode], edges: List[DiagramEdge] = None) -> str:
        """
        Generates Mermaid.js markdown syntax from nodes and edges.
        """
        if edges is None:
            edges = self.build_edges_from_spatial_layout(nodes)

        lines = [f"```mermaid\nflowchart {self.direction}"]

        # 1. Define nodes with clean labels
        lines.append("    %% Node Definitions")
        for node in nodes:
            # Sanitize text for Mermaid syntax
            clean_label = node.text.replace('"', "'").replace("\n", " ").strip()
            # If text has trailing dash-like or punctuation OCR artifacts, clean it up
            clean_label = re.sub(r"[\s\-—_.,;:|/\\]+$", "", clean_label)
            if not clean_label:
                clean_label = node.id
            lines.append(f'    {node.id}["{clean_label}"]')

        # 2. Define edges / connections
        if edges:
            lines.append("\n    %% Connections")
            for edge in edges:
                if edge.label:
                    lines.append(f'    {edge.source_id} {edge.arrow_type}|"{edge.label}"| {edge.target_id}')
                else:
                    lines.append(f'    {edge.source_id} {edge.arrow_type} {edge.target_id}')

        lines.append("```")
        return "\n".join(lines)


# -------------------------------------------------------------
# Standalone CLI Verification
# -------------------------------------------------------------
if __name__ == "__main__":
    # Test using mock data matching your exact terminal output
    mock_nodes = [
        DiagramNode(id="node_2", text="Hi", bbox=(150, 450, 60, 40), centroid=(170, 476)),
        DiagramNode(id="node_3", text="Hello", bbox=(500, 460, 70, 40), centroid=(529, 486)),
    ]

    compiler = MermaidCompiler(direction="LR")
    output_mermaid = compiler.compile(mock_nodes)

    print("\n--- COMPILED MERMAID DIAGRAM ---")
    print(output_mermaid)
    print("--------------------------------\n")