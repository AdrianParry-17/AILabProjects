"""
Graph Module

This module defines the Graph class, which is the core data structure for
representing the road network. The Graph maintains nodes, edges, and adjacency
relationships, providing an efficient API for search algorithms.

The Graph class is used by:
- All search algorithms (BFS, DFS, UCS, A*, Dijkstra, IDA*)
- Graph loader (for building the graph from CSV)
- Graph statistics (for analyzing graph properties)
- Visualization (for rendering the network)

Design Principles:
- Adjacency list representation (efficient for sparse graphs)
- O(1) node and edge lookup using dictionaries
- Clean separation between data storage and search logic
- Immutable node/edge objects, mutable graph structure

Author: AI Course Project Team
Version: 1.0.0 (Phase 3 - Graph Engine)
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from collections import deque

from .node import Node
from .edge import Edge


class Graph:
    """
    Represents a weighted directed graph for road network routing.
    
    The Graph class maintains three internal data structures for efficient
    operations:
    1. _nodes: Dictionary mapping node_id to Node objects (O(1) lookup)
    2. _adjacency: Dictionary mapping node_id to list of neighbor IDs
    3. _edges: Dictionary mapping (source, dest) tuples to Edge objects
    
    The graph supports:
    - Adding and removing nodes and edges
    - Efficient neighbor queries (critical for search algorithms)
    - Edge cost retrieval for different optimization criteria
    - Connectivity checking and graph statistics
    
    Example:
        >>> graph = Graph()
        >>> node1 = Node(1, "Warehouse", 10.8, 106.6, "Tan Binh", "warehouse", 123)
        >>> node2 = Node(2, "Market", 10.77, 106.7, "District 1", "market", 456)
        >>> graph.add_node(node1)
        >>> graph.add_node(node2)
        >>> edge = Edge(1, 1, 2, 1000, 5.0, 40, "primary", "two_way", 3, 1, 10.5)
        >>> graph.add_edge(edge)
        >>> neighbors = graph.neighbors(1)
        >>> print(neighbors)
        [(2, Edge(1: 1 → 2, 1000m))]
    
    Attributes:
        _nodes: Dictionary mapping node_id to Node objects
        _adjacency: Dictionary mapping node_id to list of neighbor node_ids
        _edges: Dictionary mapping (source, dest) tuples to Edge objects
    """
    
    def __init__(self):
        """
        Initialize an empty graph.
        
        Creates three empty dictionaries for nodes, adjacency list, and edges.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._nodes: Dict[int, Node] = {}
        self._adjacency: Dict[int, List[int]] = {}
        self._edges: Dict[Tuple[int, int], Edge] = {}
    
    # ========================================================================
    # NODE OPERATIONS
    # ========================================================================
    
    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: Node object to add
            
        Raises:
            ValueError: If a node with the same ID already exists
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> graph = Graph()
            >>> node = Node(1, "Warehouse", 10.8, 106.6, "Tan Binh", "warehouse", 123)
            >>> graph.add_node(node)
        """
        if node.node_id in self._nodes:
            raise ValueError(f"Node with ID {node.node_id} already exists")
        
        self._nodes[node.node_id] = node
        self._adjacency[node.node_id] = []
    
    def remove_node(self, node_id: int) -> None:
        """
        Remove a node and all its connected edges from the graph.
        
        This method:
        1. Removes the node from _nodes
        2. Removes all edges connected to this node
        3. Removes this node from adjacency lists of other nodes
        4. Removes the adjacency list entry for this node
        
        Args:
            node_id: ID of the node to remove
            
        Raises:
            KeyError: If node does not exist
            
        Time Complexity: O(degree) where degree is the number of connected edges
        Space Complexity: O(1)
        
        Example:
            >>> graph.remove_node(1)
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} does not exist")
        
        # Remove all edges connected to this node
        edges_to_remove = []
        for (source, dest) in self._edges.keys():
            if source == node_id or dest == node_id:
                edges_to_remove.append((source, dest))
        
        for edge_key in edges_to_remove:
            self.remove_edge(edge_key[0], edge_key[1])
        
        # Remove node and its adjacency list
        del self._nodes[node_id]
        del self._adjacency[node_id]
    
    def get_node(self, node_id: int) -> Node:
        """
        Get a node by its ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            Node object
            
        Raises:
            KeyError: If node does not exist
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> node = graph.get_node(1)
            >>> print(node.name)
            Warehouse
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} does not exist")
        return self._nodes[node_id]
    
    def contains_node(self, node_id: int) -> bool:
        """
        Check if a node exists in the graph.
        
        Args:
            node_id: ID of the node to check
            
        Returns:
            True if node exists, False otherwise
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> if graph.contains_node(1):
            ...     print("Node exists")
        """
        return node_id in self._nodes
    
    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes in the graph.
        
        Returns:
            List of all Node objects
            
        Time Complexity: O(V) where V is number of nodes
        Space Complexity: O(V) for the returned list
        
        Example:
            >>> nodes = graph.get_all_nodes()
            >>> print(f"Graph has {len(nodes)} nodes")
        """
        return list(self._nodes.values())
    
    # ========================================================================
    # EDGE OPERATIONS
    # ========================================================================
    
    def add_edge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.
        
        This method:
        1. Validates that both source and destination nodes exist
        2. Adds the edge to _edges dictionary
        3. Adds destination to source's adjacency list
        
        Args:
            edge: Edge object to add
            
        Raises:
            ValueError: If source or destination node does not exist
            ValueError: If edge already exists
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> edge = Edge(1, 1, 2, 1000, 5.0, 40, "primary", "two_way", 3, 1, 10.5)
            >>> graph.add_edge(edge)
        """
        # Validate nodes exist
        if edge.source not in self._nodes:
            raise ValueError(f"Source node {edge.source} does not exist")
        if edge.destination not in self._nodes:
            raise ValueError(f"Destination node {edge.destination} does not exist")
        
        edge_key = (edge.source, edge.destination)
        
        if edge_key in self._edges:
            raise ValueError(f"Edge from {edge.source} to {edge.destination} already exists")
        
        # Add edge
        self._edges[edge_key] = edge
        
        # Update adjacency list
        if edge.destination not in self._adjacency[edge.source]:
            self._adjacency[edge.source].append(edge.destination)
    
    def remove_edge(self, source: int, destination: int) -> None:
        """
        Remove an edge from the graph.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            
        Raises:
            KeyError: If edge does not exist
            
        Time Complexity: O(degree) for removing from adjacency list
        Space Complexity: O(1)
        
        Example:
            >>> graph.remove_edge(1, 2)
        """
        edge_key = (source, destination)
        
        if edge_key not in self._edges:
            raise KeyError(f"Edge from {source} to {destination} does not exist")
        
        # Remove edge
        del self._edges[edge_key]
        
        # Update adjacency list
        if destination in self._adjacency[source]:
            self._adjacency[source].remove(destination)
    
    def get_edge(self, source: int, destination: int) -> Edge:
        """
        Get an edge by source and destination node IDs.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            
        Returns:
            Edge object
            
        Raises:
            KeyError: If edge does not exist
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> edge = graph.get_edge(1, 2)
            >>> print(f"Distance: {edge.distance}m")
        """
        edge_key = (source, destination)
        
        if edge_key not in self._edges:
            raise KeyError(f"Edge from {source} to {destination} does not exist")
        
        return self._edges[edge_key]
    
    def contains_edge(self, source: int, destination: int) -> bool:
        """
        Check if an edge exists in the graph.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            
        Returns:
            True if edge exists, False otherwise
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> if graph.contains_edge(1, 2):
            ...     print("Edge exists")
        """
        return (source, destination) in self._edges
    
    def get_all_edges(self) -> List[Edge]:
        """
        Get all edges in the graph.
        
        Returns:
            List of all Edge objects
            
        Time Complexity: O(E) where E is number of edges
        Space Complexity: O(E) for the returned list
        
        Example:
            >>> edges = graph.get_all_edges()
            >>> print(f"Graph has {len(edges)} edges")
        """
        return list(self._edges.values())
    
    # ========================================================================
    # GRAPH QUERIES (CRITICAL FOR ALGORITHMS)
    # ========================================================================
    
    def neighbors(self, node_id: int) -> List[Tuple[int, Edge]]:
        """
        Get all neighbors of a node along with their connecting edges.
        
        This is the **most important method for search algorithms**. It returns
        both the neighbor node ID and the edge object, allowing algorithms to
        access edge costs in a single call.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of (neighbor_id, edge) tuples
            
        Raises:
            KeyError: If node does not exist
            
        Time Complexity: O(degree) where degree is the number of neighbors
        Space Complexity: O(degree) for the returned list
        
        Example:
            >>> neighbors = graph.neighbors(1)
            >>> for neighbor_id, edge in neighbors:
            ...     print(f"Neighbor: {neighbor_id}, Cost: {edge.total_cost}")
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} does not exist")
        
        result = []
        for neighbor_id in self._adjacency[node_id]:
            edge = self._edges[(node_id, neighbor_id)]
            result.append((neighbor_id, edge))
        
        return result
    
    def degree(self, node_id: int) -> int:
        """
        Get the out-degree of a node (number of outgoing edges).
        
        Args:
            node_id: ID of the node
            
        Returns:
            Number of outgoing edges
            
        Raises:
            KeyError: If node does not exist
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> deg = graph.degree(1)
            >>> print(f"Node 1 has {deg} outgoing edges")
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} does not exist")
        
        return len(self._adjacency[node_id])
    
    def in_degree(self, node_id: int) -> int:
        """
        Get the in-degree of a node (number of incoming edges).
        
        Args:
            node_id: ID of the node
            
        Returns:
            Number of incoming edges
            
        Raises:
            KeyError: If node does not exist
            
        Time Complexity: O(E) where E is total number of edges
        Space Complexity: O(1)
        
        Example:
            >>> in_deg = graph.in_degree(1)
            >>> print(f"Node 1 has {in_deg} incoming edges")
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} does not exist")
        
        count = 0
        for (source, dest) in self._edges.keys():
            if dest == node_id:
                count += 1
        
        return count
    
    # ========================================================================
    # GRAPH STATISTICS
    # ========================================================================
    
    def number_of_nodes(self) -> int:
        """
        Get the total number of nodes in the graph.
        
        Returns:
            Number of nodes
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> print(f"Graph has {graph.number_of_nodes()} nodes")
        """
        return len(self._nodes)
    
    def number_of_edges(self) -> int:
        """
        Get the total number of edges in the graph.
        
        Returns:
            Number of edges
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> print(f"Graph has {graph.number_of_edges()} edges")
        """
        return len(self._edges)
    
    def is_empty(self) -> bool:
        """
        Check if the graph is empty (has no nodes).
        
        Returns:
            True if graph has no nodes, False otherwise
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return len(self._nodes) == 0
    
    def is_connected(self) -> bool:
        """
        Check if the graph is weakly connected (ignoring edge directions).
        
        A graph is weakly connected if there is a path between every pair of
        nodes when treating all edges as undirected.
        
        Uses BFS to check connectivity from the first node.
        
        Returns:
            True if graph is weakly connected, False otherwise
            
        Time Complexity: O(V + E) where V is nodes, E is edges
        Space Complexity: O(V) for BFS queue and visited set
        
        Example:
            >>> if graph.is_connected():
            ...     print("Graph is connected")
            ... else:
            ...     print("Graph is disconnected")
        """
        if self.is_empty():
            return True
        
        # Build undirected adjacency for BFS
        undirected_adj: Dict[int, Set[int]] = {node_id: set() for node_id in self._nodes}
        
        for (source, dest) in self._edges.keys():
            undirected_adj[source].add(dest)
            undirected_adj[dest].add(source)
        
        # BFS from first node
        start_node = next(iter(self._nodes.keys()))
        visited = set()
        queue = deque([start_node])
        visited.add(start_node)
        
        while queue:
            current = queue.popleft()
            
            for neighbor in undirected_adj[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Check if all nodes were visited
        return len(visited) == len(self._nodes)
    
    def get_connected_components(self) -> List[Set[int]]:
        """
        Find all weakly connected components in the graph.
        
        Returns:
            List of sets, where each set contains node IDs in one component
            
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        
        Example:
            >>> components = graph.get_connected_components()
            >>> print(f"Graph has {len(components)} connected components")
        """
        if self.is_empty():
            return []
        
        # Build undirected adjacency
        undirected_adj: Dict[int, Set[int]] = {node_id: set() for node_id in self._nodes}
        
        for (source, dest) in self._edges.keys():
            undirected_adj[source].add(dest)
            undirected_adj[dest].add(source)
        
        # Find components using BFS
        visited = set()
        components = []
        
        for node_id in self._nodes.keys():
            if node_id not in visited:
                # BFS to find all nodes in this component
                component = set()
                queue = deque([node_id])
                visited.add(node_id)
                component.add(node_id)
                
                while queue:
                    current = queue.popleft()
                    
                    for neighbor in undirected_adj[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
                
                components.append(component)
        
        return components
    
    def statistics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics about the graph.
        
        Returns:
            Dictionary containing:
            - num_nodes: Total number of nodes
            - num_edges: Total number of edges
            - avg_degree: Average out-degree
            - max_degree: Maximum out-degree
            - min_degree: Minimum out-degree
            - density: Graph density (edges / possible edges)
            - is_connected: Whether graph is weakly connected
            - num_components: Number of connected components
            
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        
        Example:
            >>> stats = graph.statistics()
            >>> print(f"Nodes: {stats['num_nodes']}")
            >>> print(f"Edges: {stats['num_edges']}")
            >>> print(f"Connected: {stats['is_connected']}")
        """
        if self.is_empty():
            return {
                'num_nodes': 0,
                'num_edges': 0,
                'avg_degree': 0,
                'max_degree': 0,
                'min_degree': 0,
                'density': 0,
                'is_connected': True,
                'num_components': 0
            }
        
        # Calculate degrees
        degrees = [self.degree(node_id) for node_id in self._nodes.keys()]
        
        # Calculate density
        num_nodes = len(self._nodes)
        num_edges = len(self._edges)
        max_possible_edges = num_nodes * (num_nodes - 1)  # Directed graph
        density = num_edges / max_possible_edges if max_possible_edges > 0 else 0
        
        # Check connectivity
        is_connected = self.is_connected()
        components = self.get_connected_components()
        
        return {
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'avg_degree': sum(degrees) / len(degrees) if degrees else 0,
            'max_degree': max(degrees) if degrees else 0,
            'min_degree': min(degrees) if degrees else 0,
            'density': density,
            'is_connected': is_connected,
            'num_components': len(components)
        }
    
    def print_statistics(self) -> None:
        """
        Print formatted graph statistics.
        
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        """
        stats = self.statistics()
        
        print("\n" + "=" * 70)
        print("GRAPH STATISTICS")
        print("=" * 70)
        print(f"Number of nodes:        {stats['num_nodes']}")
        print(f"Number of edges:        {stats['num_edges']}")
        print(f"Average degree:         {stats['avg_degree']:.2f}")
        print(f"Maximum degree:         {stats['max_degree']}")
        print(f"Minimum degree:         {stats['min_degree']}")
        print(f"Graph density:          {stats['density']:.4f}")
        print(f"Is connected:           {stats['is_connected']}")
        print(f"Connected components:   {stats['num_components']}")
        print("=" * 70 + "\n")
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def clear(self) -> None:
        """
        Remove all nodes and edges from the graph.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._nodes.clear()
        self._adjacency.clear()
        self._edges.clear()
    
    def copy(self) -> 'Graph':
        """
        Create a deep copy of the graph.
        
        Returns:
            New Graph object with same nodes and edges
            
        Time Complexity: O(V + E)
        Space Complexity: O(V + E)
        """
        new_graph = Graph()
        
        # Copy nodes
        for node in self._nodes.values():
            new_graph.add_node(node)
        
        # Copy edges
        for edge in self._edges.values():
            new_graph.add_edge(edge)
        
        return new_graph
    
    def __str__(self) -> str:
        """
        Human-readable string representation.
        
        Returns:
            String with node and edge counts
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return f"Graph(nodes={len(self._nodes)}, edges={len(self._edges)})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation for debugging.
        
        Returns:
            String with object details
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return f"Graph(nodes={len(self._nodes)}, edges={len(self._edges)})"
    
    def __len__(self) -> int:
        """
        Return the number of nodes in the graph.
        
        Returns:
            Number of nodes
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return len(self._nodes)
    
    def __contains__(self, node_id: int) -> bool:
        """
        Check if a node exists in the graph (supports 'in' operator).
        
        Args:
            node_id: Node ID to check
            
        Returns:
            True if node exists, False otherwise
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Example:
            >>> if 1 in graph:
            ...     print("Node 1 exists")
        """
        return node_id in self._nodes


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the Graph class."""
    print("=" * 70)
    print("TESTING GRAPH CLASS")
    print("=" * 70)
    
    # Test 1: Create empty graph
    print("\n1. Creating empty graph...")
    graph = Graph()
    print(f"✓ Created: {graph}")
    assert graph.is_empty()
    print("✓ Graph is empty")
    
    # Test 2: Add nodes
    print("\n2. Adding nodes...")
    node1 = Node(1, "Warehouse", 10.8025, 106.6545, "Tan Binh", "warehouse", 123)
    node2 = Node(2, "Market", 10.7725, 106.6980, "District 1", "market", 456)
    node3 = Node(3, "Hospital", 10.7620, 106.6780, "District 5", "hospital", 789)
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    print(f"✓ Added 3 nodes: {graph}")
    
    # Test 3: Get nodes
    print("\n3. Getting nodes...")
    retrieved_node = graph.get_node(1)
    print(f"✓ Retrieved: {retrieved_node}")
    assert retrieved_node.name == "Warehouse"
    
    # Test 4: Check node existence
    print("\n4. Checking node existence...")
    assert graph.contains_node(1)
    assert not graph.contains_node(99)
    print("✓ Node existence checks passed")
    
    # Test 5: Add edges
    print("\n5. Adding edges...")
    edge1 = Edge(1, 1, 2, 1000, 5.0, 40, "primary", "two_way", 3, 1, 10.5)
    edge2 = Edge(2, 2, 3, 800, 4.0, 40, "secondary", "two_way", 2, 1, 8.2)
    edge3 = Edge(3, 1, 3, 1500, 7.5, 50, "primary", "two_way", 4, 2, 15.3)
    
    graph.add_edge(edge1)
    graph.add_edge(edge2)
    graph.add_edge(edge3)
    print(f"✓ Added 3 edges: {graph}")
    
    # Test 6: Get edges
    print("\n6. Getting edges...")
    retrieved_edge = graph.get_edge(1, 2)
    print(f"✓ Retrieved: {retrieved_edge}")
    assert retrieved_edge.distance == 1000
    
    # Test 7: Get neighbors (CRITICAL FOR ALGORITHMS)
    print("\n7. Getting neighbors...")
    neighbors = graph.neighbors(1)
    print(f"✓ Node 1 has {len(neighbors)} neighbors:")
    for neighbor_id, edge in neighbors:
        neighbor_node = graph.get_node(neighbor_id)
        print(f"  - {neighbor_node.name} (ID: {neighbor_id}), Distance: {edge.distance}m")
    
    # Test 8: Degree
    print("\n8. Checking degrees...")
    deg1 = graph.degree(1)
    deg2 = graph.degree(2)
    print(f"✓ Node 1 out-degree: {deg1}")
    print(f"✓ Node 2 out-degree: {deg2}")
    assert deg1 == 2  # Node 1 connects to 2 and 3
    assert deg2 == 1  # Node 2 connects to 3
    
    # Test 9: Statistics
    print("\n9. Getting statistics...")
    graph.print_statistics()
    
    # Test 10: Connectivity
    print("\n10. Checking connectivity...")
    is_connected = graph.is_connected()
    print(f"✓ Graph is connected: {is_connected}")
    assert is_connected
    
    # Test 11: Connected components
    print("\n11. Finding connected components...")
    components = graph.get_connected_components()
    print(f"✓ Number of components: {len(components)}")
    for i, component in enumerate(components, 1):
        print(f"  Component {i}: {sorted(component)}")
    
    # Test 12: Remove edge
    print("\n12. Removing edge...")
    graph.remove_edge(1, 3)
    print(f"✓ Removed edge 1→3: {graph}")
    assert not graph.contains_edge(1, 3)
    assert graph.degree(1) == 1  # Now only connects to 2
    
    # Test 13: Remove node
    print("\n13. Removing node...")
    graph.remove_node(3)
    print(f"✓ Removed node 3: {graph}")
    assert not graph.contains_node(3)
    assert graph.number_of_nodes() == 2
    
    # Test 14: Test 'in' operator
    print("\n14. Testing 'in' operator...")
    assert 1 in graph
    assert 99 not in graph
    print("✓ 'in' operator works correctly")
    
    # Test 15: Test len()
    print("\n15. Testing len()...")
    assert len(graph) == 2
    print(f"✓ len(graph) = {len(graph)}")
    
    # Test 16: Test copy
    print("\n16. Testing copy...")
    graph_copy = graph.copy()
    assert graph_copy.number_of_nodes() == graph.number_of_nodes()
    assert graph_copy.number_of_edges() == graph.number_of_edges()
    print("✓ Graph copy successful")
    
    # Test 17: Test clear
    print("\n17. Testing clear...")
    graph.clear()
    assert graph.is_empty()
    print("✓ Graph cleared")
    
    # Test 18: Error handling
    print("\n18. Testing error handling...")
    try:
        graph.get_node(999)
        print("✗ Should have raised KeyError")
    except KeyError as e:
        print(f"✓ Correctly raised KeyError: {e}")
    
    try:
        duplicate_node = Node(1, "Duplicate", 10.8, 106.6, "Test", "test", 999)
        graph.add_node(node1)
        graph.add_node(duplicate_node)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("\n" + "=" * 70)
    print("✓ ALL GRAPH TESTS PASSED")
    print("=" * 70)