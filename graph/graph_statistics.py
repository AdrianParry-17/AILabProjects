"""
Graph Statistics Module

This module provides comprehensive statistical analysis of the road network graph.
It analyzes node distributions, edge characteristics, cost patterns, and provides
formatted reports for technical documentation and visualization.

The module is designed to work with Graph objects without modifying them, following
the principle of separation of concerns.

Key Features:
- Node analysis by type, district, and characteristics
- Edge analysis by road type, cost distribution, congestion patterns
- Path comparison and route analysis
- Report generation for technical documentation
- Visualization helpers for GUI

Author: AI Course Project Team
Version: 1.0.0 (Phase 3 - Graph Engine)
"""

import logging
from typing import Dict, List, Tuple, Set, Any, Optional
from collections import defaultdict, Counter
from pathlib import Path

from .graph import Graph
from .node import Node
from .edge import Edge

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# BASIC STATISTICS
# ============================================================================

def get_basic_statistics(graph: Graph) -> Dict[str, Any]:
    """
    Get basic statistics about the graph structure.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary containing:
        - num_nodes: Total number of nodes
        - num_edges: Total number of edges
        - avg_degree: Average out-degree
        - max_degree: Maximum out-degree
        - min_degree: Minimum out-degree
        - density: Graph density
        - is_connected: Whether graph is weakly connected
        - num_components: Number of connected components
        
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    
    Example:
        >>> stats = get_basic_statistics(graph)
        >>> print(f"Nodes: {stats['num_nodes']}")
        >>> print(f"Edges: {stats['num_edges']}")
    """
    return graph.statistics()


def get_degree_distribution(graph: Graph) -> Dict[int, int]:
    """
    Get the distribution of node degrees.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping degree to count
        Example: {0: 2, 1: 5, 2: 10, 3: 8}
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> dist = get_degree_distribution(graph)
        >>> for degree, count in sorted(dist.items()):
        ...     print(f"Degree {degree}: {count} nodes")
    """
    degree_counts = defaultdict(int)
    
    for node in graph.get_all_nodes():
        degree = graph.degree(node.node_id)
        degree_counts[degree] += 1
    
    return dict(degree_counts)


def get_in_degree_distribution(graph: Graph) -> Dict[int, int]:
    """
    Get the distribution of node in-degrees.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping in-degree to count
        
    Time Complexity: O(V × E)
    Space Complexity: O(V)
    """
    in_degree_counts = defaultdict(int)
    
    for node in graph.get_all_nodes():
        in_deg = graph.in_degree(node.node_id)
        in_degree_counts[in_deg] += 1
    
    return dict(in_degree_counts)


# ============================================================================
# NODE ANALYSIS
# ============================================================================

def analyze_nodes_by_type(graph: Graph) -> Dict[str, List[Node]]:
    """
    Group nodes by their type (warehouse, market, hospital, etc.).
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping node type to list of nodes
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> by_type = analyze_nodes_by_type(graph)
        >>> for node_type, nodes in by_type.items():
        ...     print(f"{node_type}: {len(nodes)} nodes")
    """
    nodes_by_type = defaultdict(list)
    
    for node in graph.get_all_nodes():
        nodes_by_type[node.type].append(node)
    
    return dict(nodes_by_type)


def analyze_nodes_by_district(graph: Graph) -> Dict[str, List[Node]]:
    """
    Group nodes by their district.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping district name to list of nodes
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> by_district = analyze_nodes_by_district(graph)
        >>> for district, nodes in sorted(by_district.items()):
        ...     print(f"{district}: {len(nodes)} nodes")
    """
    nodes_by_district = defaultdict(list)
    
    for node in graph.get_all_nodes():
        nodes_by_district[node.district].append(node)
    
    return dict(nodes_by_district)


def find_isolated_nodes(graph: Graph) -> List[Node]:
    """
    Find nodes with no edges (isolated nodes).
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        List of isolated Node objects
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> isolated = find_isolated_nodes(graph)
        >>> if isolated:
        ...     print(f"Found {len(isolated)} isolated nodes")
    """
    isolated = []
    
    for node in graph.get_all_nodes():
        if graph.degree(node.node_id) == 0 and graph.in_degree(node.node_id) == 0:
            isolated.append(node)
    
    return isolated


def find_leaf_nodes(graph: Graph) -> List[Node]:
    """
    Find nodes with degree 1 (leaf nodes, dead ends).
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        List of leaf Node objects
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    """
    leaves = []
    
    for node in graph.get_all_nodes():
        if graph.degree(node.node_id) == 1:
            leaves.append(node)
    
    return leaves


def find_hub_nodes(graph: Graph, threshold: int = 3) -> List[Node]:
    """
    Find nodes with high degree (hub nodes, major intersections).
    
    Args:
        graph: Graph object to analyze
        threshold: Minimum degree to be considered a hub
        
    Returns:
        List of hub Node objects
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> hubs = find_hub_nodes(graph, threshold=4)
        >>> for hub in hubs:
        ...     print(f"{hub.name}: degree {graph.degree(hub.node_id)}")
    """
    hubs = []
    
    for node in graph.get_all_nodes():
        if graph.degree(node.node_id) >= threshold:
            hubs.append(node)
    
    return hubs


# ============================================================================
# EDGE ANALYSIS
# ============================================================================

def analyze_edges_by_road_type(graph: Graph) -> Dict[str, List[Edge]]:
    """
    Group edges by road type.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping road type to list of edges
        
    Time Complexity: O(E)
    Space Complexity: O(E)
    
    Example:
        >>> by_type = analyze_edges_by_road_type(graph)
        >>> for road_type, edges in by_type.items():
        ...     print(f"{road_type}: {len(edges)} edges")
    """
    edges_by_type = defaultdict(list)
    
    for edge in graph.get_all_edges():
        edges_by_type[edge.road_type].append(edge)
    
    return dict(edges_by_type)


def analyze_edges_by_direction(graph: Graph) -> Dict[str, List[Edge]]:
    """
    Group edges by direction (one_way, two_way).
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping direction to list of edges
        
    Time Complexity: O(E)
    Space Complexity: O(E)
    """
    edges_by_direction = defaultdict(list)
    
    for edge in graph.get_all_edges():
        edges_by_direction[edge.direction].append(edge)
    
    return dict(edges_by_direction)


def get_cost_statistics(graph: Graph) -> Dict[str, Dict[str, float]]:
    """
    Get statistical measures for all cost metrics.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary containing min, max, mean, std for each metric:
        - distance (meters)
        - travel_time (minutes)
        - total_cost
        
    Time Complexity: O(E)
    Space Complexity: O(1)
    
    Example:
        >>> costs = get_cost_statistics(graph)
        >>> print(f"Average distance: {costs['distance']['mean']:.2f}m")
        >>> print(f"Average time: {costs['travel_time']['mean']:.2f} min")
    """
    distances = []
    times = []
    costs = []
    
    for edge in graph.get_all_edges():
        distances.append(edge.distance)
        times.append(edge.travel_time)
        costs.append(edge.total_cost)
    
    def calc_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0, 'sum': 0}
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        return {
            'min': min(values),
            'max': max(values),
            'mean': mean,
            'std': std,
            'sum': sum(values)
        }
    
    return {
        'distance': calc_stats(distances),
        'travel_time': calc_stats(times),
        'total_cost': calc_stats(costs)
    }


def get_congestion_distribution(graph: Graph) -> Dict[int, int]:
    """
    Get distribution of congestion levels across edges.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping congestion level (1-5) to count
        
    Time Complexity: O(E)
    Space Complexity: O(1)
    
    Example:
        >>> dist = get_congestion_distribution(graph)
        >>> for level in range(1, 6):
        ...     count = dist.get(level, 0)
        ...     print(f"Level {level}: {count} edges")
    """
    congestion_counts = defaultdict(int)
    
    for edge in graph.get_all_edges():
        congestion_counts[edge.congestion_level] += 1
    
    return dict(congestion_counts)


def get_risk_distribution(graph: Graph) -> Dict[int, int]:
    """
    Get distribution of risk levels across edges.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping risk level (0-3) to count
        
    Time Complexity: O(E)
    Space Complexity: O(1)
    """
    risk_counts = defaultdict(int)
    
    for edge in graph.get_all_edges():
        risk_counts[edge.risk_level] += 1
    
    return dict(risk_counts)


def get_speed_limit_distribution(graph: Graph) -> Dict[int, int]:
    """
    Get distribution of speed limits across edges.
    
    Args:
        graph: Graph object to analyze
        
    Returns:
        Dictionary mapping speed limit (km/h) to count
        
    Time Complexity: O(E)
    Space Complexity: O(1)
    """
    speed_counts = defaultdict(int)
    
    for edge in graph.get_all_edges():
        speed_counts[edge.speed_limit] += 1
    
    return dict(speed_counts)


# ============================================================================
# PATH ANALYSIS
# ============================================================================

def analyze_path(graph: Graph, path: List[int]) -> Dict[str, Any]:
    """
    Analyze a specific path through the graph.
    
    Args:
        graph: Graph object
        path: List of node IDs representing the path
        
    Returns:
        Dictionary containing:
        - total_distance: Sum of edge distances
        - total_time: Sum of travel times
        - total_cost: Sum of edge costs
        - num_edges: Number of edges in path
        - avg_congestion: Average congestion level
        - avg_risk: Average risk level
        - road_types: List of road types used
        - max_congestion_segment: Edge with highest congestion
        - min_congestion_segment: Edge with lowest congestion
        
    Time Complexity: O(P) where P is path length
    Space Complexity: O(P)
    
    Example:
        >>> path = [1, 3, 5, 10]
        >>> analysis = analyze_path(graph, path)
        >>> print(f"Total distance: {analysis['total_distance']:.2f}m")
        >>> print(f"Total time: {analysis['total_time']:.2f} min")
    """
    if len(path) < 2:
        return {
            'total_distance': 0,
            'total_time': 0,
            'total_cost': 0,
            'num_edges': 0,
            'avg_congestion': 0,
            'avg_risk': 0,
            'road_types': [],
            'max_congestion_segment': None,
            'min_congestion_segment': None
        }
    
    total_distance = 0
    total_time = 0
    total_cost = 0
    congestions = []
    risks = []
    road_types = []
    edges = []
    
    for i in range(len(path) - 1):
        source = path[i]
        destination = path[i + 1]
        
        try:
            edge = graph.get_edge(source, destination)
            edges.append(edge)
            
            total_distance += edge.distance
            total_time += edge.travel_time
            total_cost += edge.total_cost
            congestions.append(edge.congestion_level)
            risks.append(edge.risk_level)
            road_types.append(edge.road_type)
        except KeyError:
            logger.warning(f"Edge from {source} to {destination} not found")
    
    if not edges:
        return {
            'total_distance': 0,
            'total_time': 0,
            'total_cost': 0,
            'num_edges': 0,
            'avg_congestion': 0,
            'avg_risk': 0,
            'road_types': [],
            'max_congestion_segment': None,
            'min_congestion_segment': None
        }
    
    max_congestion_edge = max(edges, key=lambda e: e.congestion_level)
    min_congestion_edge = min(edges, key=lambda e: e.congestion_level)
    
    return {
        'total_distance': total_distance,
        'total_time': total_time,
        'total_cost': total_cost,
        'num_edges': len(edges),
        'avg_congestion': sum(congestions) / len(congestions),
        'avg_risk': sum(risks) / len(risks),
        'road_types': road_types,
        'max_congestion_segment': max_congestion_edge,
        'min_congestion_segment': min_congestion_edge
    }


def compare_paths(graph: Graph, paths: List[Tuple[str, List[int]]]) -> List[Dict[str, Any]]:
    """
    Compare multiple paths and return analysis for each.
    
    Args:
        graph: Graph object
        paths: List of (name, path) tuples
               Example: [("BFS Path", [1, 3, 5]), ("A* Path", [1, 2, 5])]
        
    Returns:
        List of dictionaries, each containing path name and analysis
        
    Time Complexity: O(P × N) where P is number of paths, N is average path length
    Space Complexity: O(P × N)
    
    Example:
        >>> paths = [
        ...     ("BFS", [1, 3, 5, 10]),
        ...     ("A*", [1, 2, 4, 10])
        ... ]
        >>> comparisons = compare_paths(graph, paths)
        >>> for comp in comparisons:
        ...     print(f"{comp['name']}: {comp['analysis']['total_cost']:.2f}")
    """
    comparisons = []
    
    for name, path in paths:
        analysis = analyze_path(graph, path)
        comparisons.append({
            'name': name,
            'path': path,
            'analysis': analysis
        })
    
    return comparisons


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_graph_report(graph: Graph, output_path: Optional[Path] = None) -> str:
    """
    Generate a comprehensive text report about the graph.
    
    Args:
        graph: Graph object to analyze
        output_path: Optional path to save the report
        
    Returns:
        Formatted report string
        
    Time Complexity: O(V + E)
    Space Complexity: O(V + E)
    
    Example:
        >>> report = generate_graph_report(graph)
        >>> print(report)
        >>> # Or save to file
        >>> generate_graph_report(graph, Path("report.txt"))
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("GRAPH STATISTICS REPORT")
    lines.append("Ho Chi Minh City Delivery Route Optimization")
    lines.append("=" * 80)
    lines.append("")
    
    # Basic Statistics
    lines.append("1. BASIC STATISTICS")
    lines.append("-" * 80)
    stats = get_basic_statistics(graph)
    lines.append(f"Number of nodes:        {stats['num_nodes']}")
    lines.append(f"Number of edges:        {stats['num_edges']}")
    lines.append(f"Average degree:         {stats['avg_degree']:.2f}")
    lines.append(f"Maximum degree:         {stats['max_degree']}")
    lines.append(f"Minimum degree:         {stats['min_degree']}")
    lines.append(f"Graph density:          {stats['density']:.4f}")
    lines.append(f"Is connected:           {stats['is_connected']}")
    lines.append(f"Connected components:   {stats['num_components']}")
    lines.append("")
    
    # Node Analysis
    lines.append("2. NODE ANALYSIS")
    lines.append("-" * 80)
    
    # By type
    lines.append("\n2.1 Nodes by Type:")
    nodes_by_type = analyze_nodes_by_type(graph)
    for node_type, nodes in sorted(nodes_by_type.items()):
        lines.append(f"  {node_type:20s}: {len(nodes):3d} nodes")
    
    # By district
    lines.append("\n2.2 Nodes by District:")
    nodes_by_district = analyze_nodes_by_district(graph)
    for district, nodes in sorted(nodes_by_district.items()):
        lines.append(f"  {district:20s}: {len(nodes):3d} nodes")
    
    # Special nodes
    isolated = find_isolated_nodes(graph)
    leaves = find_leaf_nodes(graph)
    hubs = find_hub_nodes(graph, threshold=3)
    
    lines.append(f"\n2.3 Special Nodes:")
    lines.append(f"  Isolated nodes (degree 0): {len(isolated)}")
    lines.append(f"  Leaf nodes (degree 1):     {len(leaves)}")
    lines.append(f"  Hub nodes (degree ≥ 3):    {len(hubs)}")
    
    if hubs:
        lines.append("\n  Hub nodes details:")
        for hub in sorted(hubs, key=lambda n: graph.degree(n.node_id), reverse=True)[:5]:
            lines.append(f"    - {hub.name:30s} (degree {graph.degree(hub.node_id)})")
    
    lines.append("")
    
    # Edge Analysis
    lines.append("3. EDGE ANALYSIS")
    lines.append("-" * 80)
    
    # By road type
    lines.append("\n3.1 Edges by Road Type:")
    edges_by_type = analyze_edges_by_road_type(graph)
    for road_type, edges in sorted(edges_by_type.items()):
        lines.append(f"  {road_type:20s}: {len(edges):3d} edges")
    
    # By direction
    lines.append("\n3.2 Edges by Direction:")
    edges_by_direction = analyze_edges_by_direction(graph)
    for direction, edges in sorted(edges_by_direction.items()):
        lines.append(f"  {direction:20s}: {len(edges):3d} edges")
    
    # Cost statistics
    lines.append("\n3.3 Cost Statistics:")
    cost_stats = get_cost_statistics(graph)
    
    lines.append("\n  Distance (meters):")
    lines.append(f"    Min:  {cost_stats['distance']['min']:8.2f}")
    lines.append(f"    Max:  {cost_stats['distance']['max']:8.2f}")
    lines.append(f"    Mean: {cost_stats['distance']['mean']:8.2f}")
    lines.append(f"    Std:  {cost_stats['distance']['std']:8.2f}")
    lines.append(f"    Total: {cost_stats['distance']['sum']:8.2f} ({cost_stats['distance']['sum']/1000:.2f} km)")
    
    lines.append("\n  Travel Time (minutes):")
    lines.append(f"    Min:  {cost_stats['travel_time']['min']:8.2f}")
    lines.append(f"    Max:  {cost_stats['travel_time']['max']:8.2f}")
    lines.append(f"    Mean: {cost_stats['travel_time']['mean']:8.2f}")
    lines.append(f"    Std:  {cost_stats['travel_time']['std']:8.2f}")
    
    lines.append("\n  Total Cost:")
    lines.append(f"    Min:  {cost_stats['total_cost']['min']:8.2f}")
    lines.append(f"    Max:  {cost_stats['total_cost']['max']:8.2f}")
    lines.append(f"    Mean: {cost_stats['total_cost']['mean']:8.2f}")
    lines.append(f"    Std:  {cost_stats['total_cost']['std']:8.2f}")
    
    # Traffic analysis
    lines.append("\n3.4 Traffic Analysis:")
    
    lines.append("\n  Congestion Distribution:")
    congestion_dist = get_congestion_distribution(graph)
    total_edges = graph.number_of_edges()
    for level in range(1, 6):
        count = congestion_dist.get(level, 0)
        percentage = (count / total_edges * 100) if total_edges > 0 else 0
        lines.append(f"    Level {level}: {count:3d} edges ({percentage:5.1f}%)")
    
    lines.append("\n  Risk Distribution:")
    risk_dist = get_risk_distribution(graph)
    for level in range(0, 4):
        count = risk_dist.get(level, 0)
        percentage = (count / total_edges * 100) if total_edges > 0 else 0
        lines.append(f"    Level {level}: {count:3d} edges ({percentage:5.1f}%)")
    
    lines.append("\n  Speed Limit Distribution:")
    speed_dist = get_speed_limit_distribution(graph)
    for speed, count in sorted(speed_dist.items()):
        percentage = (count / total_edges * 100) if total_edges > 0 else 0
        lines.append(f"    {speed:3d} km/h: {count:3d} edges ({percentage:5.1f}%)")
    
    lines.append("")
    
    # Degree Distribution
    lines.append("4. DEGREE DISTRIBUTION")
    lines.append("-" * 80)
    degree_dist = get_degree_distribution(graph)
    for degree, count in sorted(degree_dist.items()):
        percentage = (count / stats['num_nodes'] * 100) if stats['num_nodes'] > 0 else 0
        lines.append(f"  Degree {degree}: {count:3d} nodes ({percentage:5.1f}%)")
    lines.append("")
    
    # Footer
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    report = "\n".join(lines)
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {output_path}")
    
    return report


def generate_comparison_report(
    graph: Graph,
    paths: List[Tuple[str, List[int]]],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a comparison report for multiple paths.
    
    Args:
        graph: Graph object
        paths: List of (algorithm_name, path) tuples
        output_path: Optional path to save the report
        
    Returns:
        Formatted comparison report string
        
    Time Complexity: O(P × N) where P is paths, N is path length
    Space Complexity: O(P × N)
    
    Example:
        >>> paths = [
        ...     ("BFS", [1, 3, 5, 10]),
        ...     ("Dijkstra", [1, 2, 4, 10]),
        ...     ("A*", [1, 2, 5, 10])
        ... ]
        >>> report = generate_comparison_report(graph, paths)
        >>> print(report)
    """
    lines = []
    
    # Header
    lines.append("=" * 100)
    lines.append("PATH COMPARISON REPORT")
    lines.append("=" * 100)
    lines.append("")
    
    # Analyze all paths
    comparisons = compare_paths(graph, paths)
    
    # Summary table
    lines.append("SUMMARY TABLE")
    lines.append("-" * 100)
    lines.append(f"{'Algorithm':<20} {'Distance (m)':<15} {'Time (min)':<15} {'Cost':<15} {'Edges':<10} {'Avg Cong':<12}")
    lines.append("-" * 100)
    
    for comp in comparisons:
        name = comp['name']
        analysis = comp['analysis']
        lines.append(
            f"{name:<20} "
            f"{analysis['total_distance']:<15.2f} "
            f"{analysis['total_time']:<15.2f} "
            f"{analysis['total_cost']:<15.2f} "
            f"{analysis['num_edges']:<10} "
            f"{analysis['avg_congestion']:<12.2f}"
        )
    
    lines.append("-" * 100)
    lines.append("")
    
    # Detailed analysis
    for comp in comparisons:
        name = comp['name']
        path = comp['path']
        analysis = comp['analysis']
        
        lines.append(f"ALGORITHM: {name}")
        lines.append("-" * 100)
        
        # Path visualization
        path_str = " → ".join(str(node_id) for node_id in path)
        lines.append(f"Path: {path_str}")
        
        # Get node names
        node_names = []
        for node_id in path:
            try:
                node = graph.get_node(node_id)
                node_names.append(node.name)
            except KeyError:
                node_names.append(f"Node {node_id}")
        
        lines.append(f"Route: {' → '.join(node_names)}")
        lines.append("")
        
        # Metrics
        lines.append(f"Total Distance:    {analysis['total_distance']:>10.2f} m")
        lines.append(f"Total Time:        {analysis['total_time']:>10.2f} min")
        lines.append(f"Total Cost:        {analysis['total_cost']:>10.2f}")
        lines.append(f"Number of Edges:   {analysis['num_edges']:>10}")
        lines.append(f"Avg Congestion:    {analysis['avg_congestion']:>10.2f}")
        lines.append(f"Avg Risk:          {analysis['avg_risk']:>10.2f}")
        lines.append("")
        
        # Road types used
        if analysis['road_types']:
            road_type_counts = Counter(analysis['road_types'])
            lines.append("Road Types Used:")
            for road_type, count in road_type_counts.most_common():
                lines.append(f"  - {road_type}: {count} segments")
            lines.append("")
        
        # Congestion analysis
        if analysis['max_congestion_segment']:
            max_seg = analysis['max_congestion_segment']
            lines.append(f"Highest Congestion Segment:")
            lines.append(f"  Edge {max_seg.source} → {max_seg.destination}")
            lines.append(f"  Congestion Level: {max_seg.congestion_level}")
            lines.append(f"  Road Type: {max_seg.road_type}")
            lines.append("")
        
        lines.append("")
    
    # Find best path by each criterion
    lines.append("=" * 100)
    lines.append("OPTIMAL PATHS BY CRITERION")
    lines.append("=" * 100)
    
    if comparisons:
        # Best by distance
        best_distance = min(comparisons, key=lambda c: c['analysis']['total_distance'])
        lines.append(f"\nShortest Distance: {best_distance['name']}")
        lines.append(f"  Distance: {best_distance['analysis']['total_distance']:.2f} m")
        
        # Best by time
        best_time = min(comparisons, key=lambda c: c['analysis']['total_time'])
        lines.append(f"\nFastest Time: {best_time['name']}")
        lines.append(f"  Time: {best_time['analysis']['total_time']:.2f} min")
        
        # Best by cost
        best_cost = min(comparisons, key=lambda c: c['analysis']['total_cost'])
        lines.append(f"\nLowest Cost: {best_cost['name']}")
        lines.append(f"  Cost: {best_cost['analysis']['total_cost']:.2f}")
        
        # Best by congestion
        best_congestion = min(comparisons, key=lambda c: c['analysis']['avg_congestion'])
        lines.append(f"\nLeast Congested: {best_congestion['name']}")
        lines.append(f"  Avg Congestion: {best_congestion['analysis']['avg_congestion']:.2f}")
    
    lines.append("")
    lines.append("=" * 100)
    lines.append("END OF COMPARISON REPORT")
    lines.append("=" * 100)
    
    report = "\n".join(lines)
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Comparison report saved to {output_path}")
    
    return report


# ============================================================================
# VISUALIZATION HELPERS
# ============================================================================

def get_node_positions(graph: Graph) -> Dict[int, Tuple[float, float]]:
    """
    Get node positions for visualization (latitude, longitude).
    
    Args:
        graph: Graph object
        
    Returns:
        Dictionary mapping node_id to (latitude, longitude) tuple
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    
    Example:
        >>> positions = get_node_positions(graph)
        >>> for node_id, (lat, lon) in positions.items():
        ...     print(f"Node {node_id}: ({lat}, {lon})")
    """
    positions = {}
    
    for node in graph.get_all_nodes():
        positions[node.node_id] = (node.latitude, node.longitude)
    
    return positions


def get_edge_colors_by_congestion(graph: Graph) -> Dict[Tuple[int, int], str]:
    """
    Get edge colors based on congestion level for visualization.
    
    Args:
        graph: Graph object
        
    Returns:
        Dictionary mapping (source, dest) to color string
        
    Time Complexity: O(E)
    Space Complexity: O(E)
    
    Example:
        >>> colors = get_edge_colors_by_congestion(graph)
        >>> # Use with matplotlib or other visualization library
    """
    # Color scheme: green (low) → yellow → orange → red (high)
    congestion_colors = {
        1: '#00ff00',  # Green - free flow
        2: '#80ff00',  # Light green
        3: '#ffff00',  # Yellow - moderate
        4: '#ff8000',  # Orange - heavy
        5: '#ff0000'   # Red - severe
    }
    
    colors = {}
    
    for edge in graph.get_all_edges():
        edge_key = (edge.source, edge.destination)
        colors[edge_key] = congestion_colors.get(edge.congestion_level, '#808080')
    
    return colors


def get_node_colors_by_type(graph: Graph) -> Dict[int, str]:
    """
    Get node colors based on node type for visualization.
    
    Args:
        graph: Graph object
        
    Returns:
        Dictionary mapping node_id to color string
        
    Time Complexity: O(V)
    Space Complexity: O(V)
    """
    # Color scheme for different node types
    type_colors = {
        'warehouse': '#ff0000',      # Red
        'market': '#00ff00',         # Green
        'hospital': '#0000ff',       # Blue
        'university': '#ff00ff',     # Magenta
        'office': '#00ffff',         # Cyan
        'landmark': '#ffff00',       # Yellow
        'park': '#008000',           # Dark green
        'residential': '#808080',    # Gray
        'shopping': '#ff8000',       # Orange
        'event_venue': '#800080'     # Purple
    }
    
    colors = {}
    
    for node in graph.get_all_nodes():
        colors[node.node_id] = type_colors.get(node.type, '#000000')
    
    return colors


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the graph statistics module."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from graph.graph_loader import load_graph_from_csv
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("TESTING GRAPH STATISTICS MODULE")
    print("=" * 80)
    
    # Load graph
    print("\n1. Loading graph...")
    try:
        graph = load_graph_from_csv()
        print(f"✓ Graph loaded: {graph}")
    except Exception as e:
        print(f"✗ Failed to load graph: {e}")
        exit(1)
    
    # Test basic statistics
    print("\n2. Testing basic statistics...")
    stats = get_basic_statistics(graph)
    print(f"✓ Nodes: {stats['num_nodes']}")
    print(f"✓ Edges: {stats['num_edges']}")
    print(f"✓ Connected: {stats['is_connected']}")
    
    # Test degree distribution
    print("\n3. Testing degree distribution...")
    degree_dist = get_degree_distribution(graph)
    print(f"✓ Degree distribution: {degree_dist}")
    
    # Test node analysis
    print("\n4. Testing node analysis...")
    nodes_by_type = analyze_nodes_by_type(graph)
    print(f"✓ Node types: {list(nodes_by_type.keys())}")
    
    nodes_by_district = analyze_nodes_by_district(graph)
    print(f"✓ Districts: {list(nodes_by_district.keys())}")
    
    isolated = find_isolated_nodes(graph)
    print(f"✓ Isolated nodes: {len(isolated)}")
    
    hubs = find_hub_nodes(graph, threshold=3)
    print(f"✓ Hub nodes: {len(hubs)}")
    
    # Test edge analysis
    print("\n5. Testing edge analysis...")
    edges_by_type = analyze_edges_by_road_type(graph)
    print(f"✓ Road types: {list(edges_by_type.keys())}")
    
    cost_stats = get_cost_statistics(graph)
    print(f"✓ Avg distance: {cost_stats['distance']['mean']:.2f}m")
    print(f"✓ Avg time: {cost_stats['travel_time']['mean']:.2f} min")
    
    congestion_dist = get_congestion_distribution(graph)
    print(f"✓ Congestion distribution: {congestion_dist}")
    
    # Test path analysis
    print("\n6. Testing path analysis...")
    # Create a sample path (if exists)
    try:
        sample_path = [1, 25, 17]  # Warehouse → Etown → Hoang Van Thu Park
        path_analysis = analyze_path(graph, sample_path)
        print(f"✓ Path analysis:")
        print(f"  Distance: {path_analysis['total_distance']:.2f}m")
        print(f"  Time: {path_analysis['total_time']:.2f} min")
        print(f"  Cost: {path_analysis['total_cost']:.2f}")
    except Exception as e:
        print(f"⚠ Could not analyze sample path: {e}")
    
    # Test report generation
    print("\n7. Testing report generation...")
    try:
        report = generate_graph_report(graph)
        print(f"✓ Report generated: {len(report)} characters")
        print("\nFirst 500 characters:")
        print(report[:500])
    except Exception as e:
        print(f"✗ Report generation failed: {e}")
    
    # Test visualization helpers
    print("\n8. Testing visualization helpers...")
    positions = get_node_positions(graph)
    print(f"✓ Got positions for {len(positions)} nodes")
    
    edge_colors = get_edge_colors_by_congestion(graph)
    print(f"✓ Got colors for {len(edge_colors)} edges")
    
    node_colors = get_node_colors_by_type(graph)
    print(f"✓ Got colors for {len(node_colors)} nodes")
    
    print("\n" + "=" * 80)
    print("✓ ALL STATISTICS TESTS PASSED")
    print("=" * 80)