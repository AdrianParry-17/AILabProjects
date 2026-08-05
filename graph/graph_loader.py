"""
Graph Loader Module

This module provides functionality to load graph data from CSV files and
construct a Graph object. It handles file I/O, data parsing, validation,
and graph construction.

The loader is the bridge between persistent storage (CSV files) and the
in-memory graph structure used by search algorithms.

Design Principles:
- Separation of concerns: Loader handles I/O, Graph handles structure
- Fail-fast validation: Check data integrity before building graph
- Clear error messages: Help users debug data issues
- Atomic operation: Graph is either fully loaded or not loaded at all

Author: AI Course Project Team
Version: 1.0.0 (Phase 3 - Graph Engine)
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd

from .node import Node, validate_nodes
from .edge import Edge, validate_edges
from .graph import Graph

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_csv_structure(df: pd.DataFrame, required_columns: List[str], file_name: str) -> None:
    """
    Validate that a CSV file has the required column structure.
    
    Args:
        df: DataFrame loaded from CSV
        required_columns: List of required column names
        file_name: Name of the file (for error messages)
        
    Raises:
        ValueError: If required columns are missing
        
    Time Complexity: O(C) where C is number of required columns
    Space Complexity: O(C)
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"File '{file_name}' is missing required columns: {missing_columns}\n"
            f"Found columns: {list(df.columns)}\n"
            f"Required columns: {required_columns}"
        )
    
    logger.debug(f"✓ {file_name} has correct structure: {required_columns}")


def validate_no_duplicates(df: pd.DataFrame, id_column: str, file_name: str) -> None:
    """
    Validate that there are no duplicate IDs in the data.
    
    Args:
        df: DataFrame to check
        id_column: Name of the ID column
        file_name: Name of the file (for error messages)
        
    Raises:
        ValueError: If duplicate IDs are found
        
    Time Complexity: O(N) where N is number of rows
    Space Complexity: O(N)
    """
    duplicates = df[df.duplicated(subset=[id_column], keep=False)]
    
    if not duplicates.empty:
        duplicate_ids = duplicates[id_column].tolist()
        raise ValueError(
            f"File '{file_name}' contains duplicate {id_column}s: {duplicate_ids}\n"
            f"Each {id_column} must be unique."
        )
    
    logger.debug(f"✓ {file_name} has no duplicate {id_column}s")


def validate_node_references(edges_df: pd.DataFrame, node_ids: set) -> None:
    """
    Validate that all edge source and destination nodes exist.
    
    Args:
        edges_df: DataFrame containing edge data
        node_ids: Set of valid node IDs
        
    Raises:
        ValueError: If edges reference non-existent nodes
        
    Time Complexity: O(E) where E is number of edges
    Space Complexity: O(E)
    """
    # Check source nodes
    invalid_sources = set(edges_df['source']) - node_ids
    if invalid_sources:
        raise ValueError(
            f"Edges reference non-existent source nodes: {sorted(invalid_sources)}\n"
            f"Valid node IDs: {sorted(node_ids)}"
        )
    
    # Check destination nodes
    invalid_destinations = set(edges_df['destination']) - node_ids
    if invalid_destinations:
        raise ValueError(
            f"Edges reference non-existent destination nodes: {sorted(invalid_destinations)}\n"
            f"Valid node IDs: {sorted(node_ids)}"
        )
    
    logger.debug(f"✓ All edge references are valid")


# ============================================================================
# LOADING FUNCTIONS
# ============================================================================

def load_nodes_from_csv(csv_path: Path) -> List[Node]:
    """
    Load nodes from a CSV file.
    
    This function:
    1. Reads the CSV file using pandas
    2. Validates the structure (required columns)
    3. Checks for duplicate node IDs
    4. Converts each row to a Node object
    5. Validates the list of nodes
    
    Args:
        csv_path: Path to the nodes.csv file
        
    Returns:
        List of Node objects
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If data is invalid
        
    Time Complexity: O(N) where N is number of nodes
    Space Complexity: O(N)
    
    Example:
        >>> nodes = load_nodes_from_csv(Path("data/nodes.csv"))
        >>> print(f"Loaded {len(nodes)} nodes")
    """
    logger.info(f"Loading nodes from {csv_path}...")
    
    # Check file exists
    if not csv_path.exists():
        raise FileNotFoundError(f"Nodes file not found: {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read {csv_path}: {e}")
    
    logger.info(f"  Read {len(df)} rows from {csv_path.name}")
    
    # Validate structure
    required_columns = ['node_id', 'name', 'latitude', 'longitude', 'district', 'type', 'osm_id']
    validate_csv_structure(df, required_columns, csv_path.name)
    
    # Validate no duplicates
    validate_no_duplicates(df, 'node_id', csv_path.name)
    
    # Convert to Node objects
    nodes = []
    for idx, row in df.iterrows():
        try:
            node_data = row.to_dict()
            node = Node.from_dict(node_data)
            nodes.append(node)
        except Exception as e:
            raise ValueError(f"Failed to create node at row {idx}: {e}\nRow data: {row.to_dict()}")
    
    logger.info(f"  Created {len(nodes)} Node objects")
    
    # Validate nodes
    is_valid, errors = validate_nodes(nodes)
    if not is_valid:
        error_msg = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"Node validation failed:\n{error_msg}")
    
    logger.info(f"✓ Loaded and validated {len(nodes)} nodes")
    return nodes


def load_edges_from_csv(csv_path: Path) -> List[Edge]:
    """
    Load edges from a CSV file.
    
    This function:
    1. Reads the CSV file using pandas
    2. Validates the structure (required columns)
    3. Checks for duplicate edge IDs
    4. Converts each row to an Edge object
    5. Validates the list of edges
    
    Args:
        csv_path: Path to the edges.csv file
        
    Returns:
        List of Edge objects
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If data is invalid
        
    Time Complexity: O(E) where E is number of edges
    Space Complexity: O(E)
    
    Example:
        >>> edges = load_edges_from_csv(Path("data/edges.csv"))
        >>> print(f"Loaded {len(edges)} edges")
    """
    logger.info(f"Loading edges from {csv_path}...")
    
    # Check file exists
    if not csv_path.exists():
        raise FileNotFoundError(f"Edges file not found: {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read {csv_path}: {e}")
    
    logger.info(f"  Read {len(df)} rows from {csv_path.name}")
    
    # Validate structure
    required_columns = [
        'edge_id', 'source', 'destination', 'distance', 'travel_time',
        'speed_limit', 'road_type', 'direction', 'congestion_level',
        'risk_level', 'total_cost'
    ]
    validate_csv_structure(df, required_columns, csv_path.name)
    
    # Validate no duplicates
    validate_no_duplicates(df, 'edge_id', csv_path.name)
    
    # Convert to Edge objects
    edges = []
    for idx, row in df.iterrows():
        try:
            edge_data = row.to_dict()
            edge = Edge.from_dict(edge_data)
            edges.append(edge)
        except Exception as e:
            raise ValueError(f"Failed to create edge at row {idx}: {e}\nRow data: {row.to_dict()}")
    
    logger.info(f"  Created {len(edges)} Edge objects")
    
    # Validate edges
    is_valid, errors = validate_edges(edges)
    if not is_valid:
        error_msg = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"Edge validation failed:\n{error_msg}")
    
    logger.info(f"✓ Loaded and validated {len(edges)} edges")
    return edges


def load_graph_from_csv(
    nodes_csv_path: Optional[Path] = None,
    edges_csv_path: Optional[Path] = None,
    data_dir: Optional[Path] = None
) -> Graph:
    """
    Load a complete graph from CSV files.
    
    This is the main entry point for loading graph data. It:
    1. Determines file paths (uses defaults if not specified)
    2. Loads and validates nodes
    3. Loads and validates edges
    4. Validates that edges reference valid nodes
    5. Constructs and returns a Graph object
    
    Args:
        nodes_csv_path: Path to nodes.csv (default: data/nodes.csv)
        edges_csv_path: Path to edges.csv (default: data/edges.csv)
        data_dir: Alternative way to specify data directory
                  (uses data/nodes.csv and data/edges.csv)
        
    Returns:
        Fully constructed Graph object ready for use by algorithms
        
    Raises:
        FileNotFoundError: If CSV files do not exist
        ValueError: If data is invalid or inconsistent
        
    Time Complexity: O(N + E) where N is nodes, E is edges
    Space Complexity: O(N + E)
    
    Example:
        >>> # Using default paths
        >>> graph = load_graph_from_csv()
        
        >>> # Using custom paths
        >>> graph = load_graph_from_csv(
        ...     nodes_csv_path=Path("custom/nodes.csv"),
        ...     edges_csv_path=Path("custom/edges.csv")
        ... )
        
        >>> # Using data directory
        >>> graph = load_graph_from_csv(data_dir=Path("my_data"))
    """
    logger.info("=" * 70)
    logger.info("LOADING GRAPH FROM CSV FILES")
    logger.info("=" * 70)
    
    # Determine file paths
    if data_dir is not None:
        nodes_csv_path = data_dir / "nodes.csv"
        edges_csv_path = data_dir / "edges.csv"
    else:
        if nodes_csv_path is None:
            nodes_csv_path = Path("data/nodes.csv")
        if edges_csv_path is None:
            edges_csv_path = Path("data/edges.csv")
    
    logger.info(f"Nodes file: {nodes_csv_path}")
    logger.info(f"Edges file: {edges_csv_path}")
    
    # Load nodes
    nodes = load_nodes_from_csv(nodes_csv_path)
    
    # Load edges
    edges = load_edges_from_csv(edges_csv_path)
    
    # Validate edge references
    logger.info("Validating edge references...")
    node_ids = {node.node_id for node in nodes}
    validate_node_references(
        pd.read_csv(edges_csv_path),  # Re-read for validation
        node_ids
    )
    
    # Build graph
    logger.info("Building graph...")
    graph = Graph()
    
    # Add nodes
    for node in nodes:
        graph.add_node(node)
    
    logger.info(f"  Added {len(nodes)} nodes to graph")
    
    # Add edges
    for edge in edges:
        graph.add_edge(edge)
    
    logger.info(f"  Added {len(edges)} edges to graph")
    
    # Verify graph structure
    logger.info("Verifying graph structure...")
    assert graph.number_of_nodes() == len(nodes), "Node count mismatch"
    assert graph.number_of_edges() == len(edges), "Edge count mismatch"
    
    # Print statistics
    stats = graph.statistics()
    logger.info(f"✓ Graph loaded successfully!")
    logger.info(f"  Nodes: {stats['num_nodes']}")
    logger.info(f"  Edges: {stats['num_edges']}")
    logger.info(f"  Connected: {stats['is_connected']}")
    logger.info(f"  Components: {stats['num_components']}")
    
    logger.info("=" * 70)
    
    return graph


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_default_data_paths() -> Tuple[Path, Path]:
    """
    Get the default paths for nodes.csv and edges.csv.
    
    Returns:
        Tuple of (nodes_csv_path, edges_csv_path)
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    return (Path("data/nodes.csv"), Path("data/edges.csv"))


def check_data_files_exist(data_dir: Optional[Path] = None) -> bool:
    """
    Check if the required CSV files exist.
    
    Args:
        data_dir: Directory containing the CSV files (default: data/)
        
    Returns:
        True if both files exist, False otherwise
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    if data_dir is None:
        data_dir = Path("data")
    
    nodes_path = data_dir / "nodes.csv"
    edges_path = data_dir / "edges.csv"
    
    return nodes_path.exists() and edges_path.exists()


def print_data_summary(graph: Graph) -> None:
    """
    Print a summary of the loaded graph data.
    
    Args:
        graph: Loaded Graph object
        
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    print("\n" + "=" * 70)
    print("GRAPH DATA SUMMARY")
    print("=" * 70)
    
    stats = graph.statistics()
    
    print(f"\nBasic Statistics:")
    print(f"  Nodes:              {stats['num_nodes']}")
    print(f"  Edges:              {stats['num_edges']}")
    print(f"  Average degree:     {stats['avg_degree']:.2f}")
    print(f"  Graph density:      {stats['density']:.4f}")
    print(f"  Is connected:       {stats['is_connected']}")
    print(f"  Components:         {stats['num_components']}")
    
    # Node type distribution
    print(f"\nNode Types:")
    node_types = {}
    for node in graph.get_all_nodes():
        node_type = node.type
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    for node_type, count in sorted(node_types.items()):
        print(f"  {node_type:20s}: {count}")
    
    # District distribution
    print(f"\nDistricts:")
    districts = {}
    for node in graph.get_all_nodes():
        district = node.district
        districts[district] = districts.get(district, 0) + 1
    
    for district, count in sorted(districts.items()):
        print(f"  {district:20s}: {count}")
    
    # Road type distribution
    print(f"\nRoad Types:")
    road_types = {}
    for edge in graph.get_all_edges():
        road_type = edge.road_type
        road_types[road_type] = road_types.get(road_type, 0) + 1
    
    for road_type, count in sorted(road_types.items()):
        print(f"  {road_type:20s}: {count}")
    
    # Cost statistics
    print(f"\nCost Statistics:")
    distances = [edge.distance for edge in graph.get_all_edges()]
    times = [edge.travel_time for edge in graph.get_all_edges()]
    costs = [edge.total_cost for edge in graph.get_all_edges()]
    
    print(f"  Distance (m):")
    print(f"    Min:  {min(distances):8.2f}")
    print(f"    Max:  {max(distances):8.2f}")
    print(f"    Mean: {sum(distances)/len(distances):8.2f}")
    
    print(f"  Travel Time (min):")
    print(f"    Min:  {min(times):8.2f}")
    print(f"    Max:  {max(times):8.2f}")
    print(f"    Mean: {sum(times)/len(times):8.2f}")
    
    print(f"  Total Cost:")
    print(f"    Min:  {min(costs):8.2f}")
    print(f"    Max:  {max(costs):8.2f}")
    print(f"    Mean: {sum(costs)/len(costs):8.2f}")
    
    print("=" * 70 + "\n")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the graph loader."""
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("TESTING GRAPH LOADER")
    print("=" * 70)
    
    # Test 1: Check if data files exist
    print("\n1. Checking data files...")
    if check_data_files_exist():
        print("✓ Data files exist")
    else:
        print("✗ Data files not found")
        print("  Please run crawler/csv_exporter.py first to generate data files")
        exit(1)
    
    # Test 2: Load graph
    print("\n2. Loading graph from CSV...")
    try:
        graph = load_graph_from_csv()
        print(f"✓ Graph loaded: {graph}")
    except Exception as e:
        print(f"✗ Failed to load graph: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Test 3: Verify graph structure
    print("\n3. Verifying graph structure...")
    stats = graph.statistics()
    print(f"  Nodes: {stats['num_nodes']}")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Connected: {stats['is_connected']}")
    
    assert stats['num_nodes'] > 0, "Graph should have nodes"
    assert stats['num_edges'] > 0, "Graph should have edges"
    print("✓ Graph structure is valid")
    
    # Test 4: Test node retrieval
    print("\n4. Testing node retrieval...")
    try:
        node1 = graph.get_node(1)
        print(f"✓ Retrieved node 1: {node1}")
    except KeyError as e:
        print(f"✗ Failed to retrieve node: {e}")
        exit(1)
    
    # Test 5: Test edge retrieval
    print("\n5. Testing edge retrieval...")
    try:
        # Find first edge
        all_edges = graph.get_all_edges()
        if all_edges:
            first_edge = all_edges[0]
            retrieved_edge = graph.get_edge(first_edge.source, first_edge.destination)
            print(f"✓ Retrieved edge: {retrieved_edge}")
    except KeyError as e:
        print(f"✗ Failed to retrieve edge: {e}")
        exit(1)
    
    # Test 6: Test neighbors
    print("\n6. Testing neighbors...")
    try:
        neighbors = graph.neighbors(1)
        print(f"✓ Node 1 has {len(neighbors)} neighbors")
        for neighbor_id, edge in neighbors[:3]:  # Show first 3
            neighbor_node = graph.get_node(neighbor_id)
            print(f"  - {neighbor_node.name} (cost: {edge.total_cost:.2f})")
    except KeyError as e:
        print(f"✗ Failed to get neighbors: {e}")
        exit(1)
    
    # Test 7: Print data summary
    print("\n7. Printing data summary...")
    print_data_summary(graph)
    
    # Test 8: Test error handling
    print("\n8. Testing error handling...")
    
    # Test missing file
    try:
        load_graph_from_csv(
            nodes_csv_path=Path("nonexistent/nodes.csv"),
            edges_csv_path=Path("nonexistent/edges.csv")
        )
        print("✗ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"✓ Correctly raised FileNotFoundError")
    
    print("\n" + "=" * 70)
    print("✓ ALL LOADER TESTS PASSED")
    print("=" * 70)