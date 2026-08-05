"""
Graph Engine Package

This package provides the core data structures and utilities for the
HCMC Delivery Route Optimization project. It includes:

- Node and Edge data models
- Graph data structure with adjacency list representation
- CSV loader for building graphs from data files
- Statistical analysis utilities
- Custom exception hierarchy

All search algorithms (BFS, DFS, UCS, A*, Dijkstra, IDA*) will use
the Graph class as their primary interface to the road network.

Author: AI Course Project Team
Version: 1.0.0 (Phase 3 - Graph Engine)
"""

# Import data models
from .node import (
    Node,
    create_node_from_dict,
    create_node_from_graph_data,
    validate_nodes,
)

from .edge import (
    Edge,
    TrafficSimulator,
    create_edge_from_dict,
    create_edge_from_graph_data,
    validate_edges,
)

# Import core graph structure
from .graph import Graph

# Import loader utilities
from .graph_loader import (
    load_graph_from_csv,
    load_nodes_from_csv,
    load_edges_from_csv,
    check_data_files_exist,
    print_data_summary,
)

# Import statistics utilities
from .graph_statistics import (
    get_basic_statistics,
    get_degree_distribution,
    get_in_degree_distribution,
    analyze_nodes_by_type,
    analyze_nodes_by_district,
    find_isolated_nodes,
    find_leaf_nodes,
    find_hub_nodes,
    analyze_edges_by_road_type,
    analyze_edges_by_direction,
    get_cost_statistics,
    get_congestion_distribution,
    get_risk_distribution,
    get_speed_limit_distribution,
    analyze_path,
    compare_paths,
    generate_graph_report,
    generate_comparison_report,
    get_node_positions,
    get_edge_colors_by_congestion,
    get_node_colors_by_type,
)

# Import exceptions
from .exceptions import (
    # Base exceptions
    GraphError,
    # Node exceptions
    NodeError,
    NodeNotFound,
    DuplicateNode,
    # Edge exceptions
    EdgeError,
    EdgeNotFound,
    DuplicateEdge,
    # Data exceptions
    DataError,
    InvalidCSV,
    ValidationError,
    # Structure exceptions
    GraphStructureError,
    InvalidGraph,
    # Algorithm exceptions
    AlgorithmError,
    PathNotFound,
    InvalidStartNode,
    InvalidGoalNode,
    # Utility functions
    get_exception_hierarchy,
    format_exception_for_user,
)

# Define public API
__all__ = [
    # Data Models
    "Node",
    "Edge",
    "Graph",
    
    # Node utilities
    "create_node_from_dict",
    "create_node_from_graph_data",
    "validate_nodes",
    
    # Edge utilities
    "TrafficSimulator",
    "create_edge_from_dict",
    "create_edge_from_graph_data",
    "validate_edges",
    
    # Loader utilities
    "load_graph_from_csv",
    "load_nodes_from_csv",
    "load_edges_from_csv",
    "check_data_files_exist",
    "print_data_summary",
    
    # Statistics utilities
    "get_basic_statistics",
    "get_degree_distribution",
    "get_in_degree_distribution",
    "analyze_nodes_by_type",
    "analyze_nodes_by_district",
    "find_isolated_nodes",
    "find_leaf_nodes",
    "find_hub_nodes",
    "analyze_edges_by_road_type",
    "analyze_edges_by_direction",
    "get_cost_statistics",
    "get_congestion_distribution",
    "get_risk_distribution",
    "get_speed_limit_distribution",
    "analyze_path",
    "compare_paths",
    "generate_graph_report",
    "generate_comparison_report",
    "get_node_positions",
    "get_edge_colors_by_congestion",
    "get_node_colors_by_type",
    
    # Exceptions
    "GraphError",
    "NodeError",
    "NodeNotFound",
    "DuplicateNode",
    "EdgeError",
    "EdgeNotFound",
    "DuplicateEdge",
    "DataError",
    "InvalidCSV",
    "ValidationError",
    "GraphStructureError",
    "InvalidGraph",
    "AlgorithmError",
    "PathNotFound",
    "InvalidStartNode",
    "InvalidGoalNode",
    "get_exception_hierarchy",
    "format_exception_for_user",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "AI Course Project Team"
__description__ = "Graph Engine for HCMC Delivery Route Optimization"