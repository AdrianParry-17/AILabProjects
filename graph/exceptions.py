"""
Graph Exceptions Module

This module defines a hierarchy of custom exceptions for the Graph Engine.
Custom exceptions provide clear, specific error messages and enable precise
error handling throughout the application.

Exception Hierarchy:
    GraphError (base class for all graph-related errors)
    ├── NodeError (errors related to nodes)
    │   ├── NodeNotFound (node does not exist)
    │   └── DuplicateNode (node already exists)
    ├── EdgeError (errors related to edges)
    │   ├── EdgeNotFound (edge does not exist)
    │   └── DuplicateEdge (edge already exists)
    ├── DataError (errors related to data loading/validation)
    │   ├── InvalidCSV (CSV file is malformed)
    │   └── ValidationError (data validation failed)
    ├── GraphStructureError (errors related to graph structure)
    │   └── InvalidGraph (graph structure is invalid)
    └── AlgorithmError (errors related to search algorithms)
        └── PathNotFound (no path exists between nodes)

Usage Example:
    try:
        node = graph.get_node(999)
    except NodeNotFound as e:
        print(f"Error: {e}")
        print(f"Node ID: {e.node_id}")

Author: AI Course Project Team
Version: 1.0.0 (Phase 3 - Graph Engine)
"""

from typing import Any, Optional, List


# ============================================================================
# BASE EXCEPTION
# ============================================================================

class GraphError(Exception):
    """
    Base exception for all graph-related errors.
    
    All custom exceptions in the Graph Engine inherit from this class.
    This allows catching all graph-related errors with a single except clause.
    
    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional error context
    
    Example:
        try:
            # Some graph operation
            pass
        except GraphError as e:
            print(f"Graph error occurred: {e}")
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize the base graph exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional context
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """
        Return formatted error message with details.
        
        Returns:
            Formatted error string
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ============================================================================
# NODE EXCEPTIONS
# ============================================================================

class NodeError(GraphError):
    """
    Base exception for node-related errors.
    
    Inherits from GraphError. All node-specific exceptions should inherit
    from this class.
    """
    pass


class NodeNotFound(NodeError):
    """
    Exception raised when attempting to access a node that does not exist.
    
    Attributes:
        node_id: The ID of the node that was not found
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     node = graph.get_node(999)
        ... except NodeNotFound as e:
        ...     print(f"Node {e.node_id} not found")
        Node 999 not found
    """
    
    def __init__(self, node_id: int, message: Optional[str] = None):
        """
        Initialize NodeNotFound exception.
        
        Args:
            node_id: The ID of the node that was not found
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.node_id = node_id
        if message is None:
            message = f"Node with ID {node_id} does not exist in the graph"
        super().__init__(message, {'node_id': node_id})


class DuplicateNode(NodeError):
    """
    Exception raised when attempting to add a node that already exists.
    
    Attributes:
        node_id: The ID of the duplicate node
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     graph.add_node(existing_node)
        ... except DuplicateNode as e:
        ...     print(f"Node {e.node_id} already exists")
        Node 1 already exists
    """
    
    def __init__(self, node_id: int, message: Optional[str] = None):
        """
        Initialize DuplicateNode exception.
        
        Args:
            node_id: The ID of the duplicate node
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.node_id = node_id
        if message is None:
            message = f"Node with ID {node_id} already exists in the graph"
        super().__init__(message, {'node_id': node_id})


# ============================================================================
# EDGE EXCEPTIONS
# ============================================================================

class EdgeError(GraphError):
    """
    Base exception for edge-related errors.
    
    Inherits from GraphError. All edge-specific exceptions should inherit
    from this class.
    """
    pass


class EdgeNotFound(EdgeError):
    """
    Exception raised when attempting to access an edge that does not exist.
    
    Attributes:
        source: Source node ID
        destination: Destination node ID
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     edge = graph.get_edge(1, 99)
        ... except EdgeNotFound as e:
        ...     print(f"Edge {e.source} → {e.destination} not found")
        Edge 1 → 99 not found
    """
    
    def __init__(self, source: int, destination: int, message: Optional[str] = None):
        """
        Initialize EdgeNotFound exception.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.source = source
        self.destination = destination
        if message is None:
            message = f"Edge from node {source} to node {destination} does not exist"
        super().__init__(message, {'source': source, 'destination': destination})


class DuplicateEdge(EdgeError):
    """
    Exception raised when attempting to add an edge that already exists.
    
    Attributes:
        source: Source node ID
        destination: Destination node ID
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     graph.add_edge(existing_edge)
        ... except DuplicateEdge as e:
        ...     print(f"Edge {e.source} → {e.destination} already exists")
        Edge 1 → 2 already exists
    """
    
    def __init__(self, source: int, destination: int, message: Optional[str] = None):
        """
        Initialize DuplicateEdge exception.
        
        Args:
            source: Source node ID
            destination: Destination node ID
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.source = source
        self.destination = destination
        if message is None:
            message = f"Edge from node {source} to node {destination} already exists"
        super().__init__(message, {'source': source, 'destination': destination})


# ============================================================================
# DATA EXCEPTIONS
# ============================================================================

class DataError(GraphError):
    """
    Base exception for data loading and validation errors.
    
    Inherits from GraphError. All data-related exceptions should inherit
    from this class.
    """
    pass


class InvalidCSV(DataError):
    """
    Exception raised when a CSV file is malformed or missing required data.
    
    Attributes:
        file_path: Path to the problematic CSV file
        issue: Description of the issue
        missing_columns: List of missing column names (if applicable)
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     load_graph_from_csv("bad_file.csv")
        ... except InvalidCSV as e:
        ...     print(f"CSV error in {e.file_path}: {e.issue}")
        CSV error in data/nodes.csv: Missing required columns
    """
    
    def __init__(
        self,
        file_path: str,
        issue: str,
        missing_columns: Optional[List[str]] = None,
        message: Optional[str] = None
    ):
        """
        Initialize InvalidCSV exception.
        
        Args:
            file_path: Path to the problematic CSV file
            issue: Description of the issue
            missing_columns: List of missing column names (if applicable)
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(C) where C is number of missing columns
        """
        self.file_path = file_path
        self.issue = issue
        self.missing_columns = missing_columns or []
        
        if message is None:
            message = f"Invalid CSV file '{file_path}': {issue}"
            if self.missing_columns:
                message += f". Missing columns: {self.missing_columns}"
        
        details = {
            'file_path': file_path,
            'issue': issue
        }
        if self.missing_columns:
            details['missing_columns'] = self.missing_columns
        
        super().__init__(message, details)


class ValidationError(DataError):
    """
    Exception raised when data validation fails.
    
    Attributes:
        errors: List of validation error messages
        entity_type: Type of entity that failed validation ('node', 'edge', 'graph')
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     validate_nodes(nodes)
        ... except ValidationError as e:
        ...     for error in e.errors:
        ...         print(f"Validation error: {error}")
        Validation error: Duplicate node IDs found: {1, 2}
    """
    
    def __init__(
        self,
        errors: List[str],
        entity_type: str = "data",
        message: Optional[str] = None
    ):
        """
        Initialize ValidationError exception.
        
        Args:
            errors: List of validation error messages
            entity_type: Type of entity that failed validation
            message: Optional custom error message
        
        Time Complexity: O(E) where E is number of errors
        Space Complexity: O(E)
        """
        self.errors = errors
        self.entity_type = entity_type
        
        if message is None:
            message = f"Validation failed for {entity_type}: {len(errors)} error(s) found"
        
        super().__init__(message, {
            'entity_type': entity_type,
            'error_count': len(errors),
            'errors': errors
        })


# ============================================================================
# GRAPH STRUCTURE EXCEPTIONS
# ============================================================================

class GraphStructureError(GraphError):
    """
    Base exception for graph structure errors.
    
    Inherits from GraphError. All graph structure-related exceptions should
    inherit from this class.
    """
    pass


class InvalidGraph(GraphStructureError):
    """
    Exception raised when the graph structure is invalid.
    
    This can occur when:
    - Graph is disconnected when it should be connected
    - Graph has orphaned edges (edges to non-existent nodes)
    - Graph structure violates constraints
    
    Attributes:
        issue: Description of the structural issue
        details_dict: Additional details about the issue
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     validate_graph_structure(graph)
        ... except InvalidGraph as e:
        ...     print(f"Graph is invalid: {e.issue}")
        Graph is invalid: Graph has 3 disconnected components
    """
    
    def __init__(
        self,
        issue: str,
        details_dict: Optional[dict] = None,
        message: Optional[str] = None
    ):
        """
        Initialize InvalidGraph exception.
        
        Args:
            issue: Description of the structural issue
            details_dict: Additional details about the issue
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.issue = issue
        self.details_dict = details_dict or {}
        
        if message is None:
            message = f"Invalid graph structure: {issue}"
        
        details = {'issue': issue}
        details.update(self.details_dict)
        
        super().__init__(message, details)


# ============================================================================
# ALGORITHM EXCEPTIONS (for Phase 5)
# ============================================================================

class AlgorithmError(GraphError):
    """
    Base exception for search algorithm errors.
    
    Inherits from GraphError. All algorithm-specific exceptions should inherit
    from this class. This will be used in Phase 5 when implementing search
    algorithms.
    """
    pass


class PathNotFound(AlgorithmError):
    """
    Exception raised when no path exists between start and goal nodes.
    
    Attributes:
        start_node: Start node ID
        goal_node: Goal node ID
        algorithm: Name of the algorithm that failed to find a path
        message: Human-readable error message
    
    Example:
        >>> try:
        ...     path = bfs(graph, start=1, goal=999)
        ... except PathNotFound as e:
        ...     print(f"No path from {e.start_node} to {e.goal_node}")
        No path from 1 to 999
    """
    
    def __init__(
        self,
        start_node: int,
        goal_node: int,
        algorithm: str = "unknown",
        message: Optional[str] = None
    ):
        """
        Initialize PathNotFound exception.
        
        Args:
            start_node: Start node ID
            goal_node: Goal node ID
            algorithm: Name of the algorithm that failed
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.start_node = start_node
        self.goal_node = goal_node
        self.algorithm = algorithm
        
        if message is None:
            message = f"No path found from node {start_node} to node {goal_node} using {algorithm}"
        
        super().__init__(message, {
            'start_node': start_node,
            'goal_node': goal_node,
            'algorithm': algorithm
        })


class InvalidStartNode(AlgorithmError):
    """
    Exception raised when the start node is invalid for an algorithm.
    
    Attributes:
        node_id: The invalid start node ID
        reason: Reason why the node is invalid
        message: Human-readable error message
    """
    
    def __init__(self, node_id: int, reason: str = "Node does not exist", message: Optional[str] = None):
        """
        Initialize InvalidStartNode exception.
        
        Args:
            node_id: The invalid start node ID
            reason: Reason why the node is invalid
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.node_id = node_id
        self.reason = reason
        
        if message is None:
            message = f"Invalid start node {node_id}: {reason}"
        
        super().__init__(message, {'node_id': node_id, 'reason': reason})


class InvalidGoalNode(AlgorithmError):
    """
    Exception raised when the goal node is invalid for an algorithm.
    
    Attributes:
        node_id: The invalid goal node ID
        reason: Reason why the node is invalid
        message: Human-readable error message
    """
    
    def __init__(self, node_id: int, reason: str = "Node does not exist", message: Optional[str] = None):
        """
        Initialize InvalidGoalNode exception.
        
        Args:
            node_id: The invalid goal node ID
            reason: Reason why the node is invalid
            message: Optional custom error message
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.node_id = node_id
        self.reason = reason
        
        if message is None:
            message = f"Invalid goal node {node_id}: {reason}"
        
        super().__init__(message, {'node_id': node_id, 'reason': reason})


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_exception_hierarchy() -> dict:
    """
    Get the complete exception hierarchy as a dictionary.
    
    Returns:
        Dictionary representing the exception hierarchy
    
    Time Complexity: O(1)
    Space Complexity: O(1)
    
    Example:
        >>> hierarchy = get_exception_hierarchy()
        >>> print(hierarchy)
    """
    return {
        'GraphError': {
            'NodeError': ['NodeNotFound', 'DuplicateNode'],
            'EdgeError': ['EdgeNotFound', 'DuplicateEdge'],
            'DataError': ['InvalidCSV', 'ValidationError'],
            'GraphStructureError': ['InvalidGraph'],
            'AlgorithmError': ['PathNotFound', 'InvalidStartNode', 'InvalidGoalNode']
        }
    }


def format_exception_for_user(exception: GraphError) -> str:
    """
    Format an exception for display to end users in the GUI.
    
    Args:
        exception: The exception to format
    
    Returns:
        User-friendly error message string
    
    Time Complexity: O(1)
    Space Complexity: O(1)
    
    Example:
        >>> try:
        ...     graph.get_node(999)
        ... except GraphError as e:
        ...     user_message = format_exception_for_user(e)
        ...     show_error_dialog(user_message)
    """
    if isinstance(exception, NodeNotFound):
        return f"❌ Node {exception.node_id} not found in the graph."
    elif isinstance(exception, EdgeNotFound):
        return f"❌ No road from node {exception.source} to node {exception.destination}."
    elif isinstance(exception, PathNotFound):
        return f"❌ No route found from node {exception.start_node} to node {exception.goal_node}."
    elif isinstance(exception, InvalidCSV):
        return f"❌ Error loading data file: {exception.issue}"
    elif isinstance(exception, ValidationError):
        return f"❌ Data validation failed with {len(exception.errors)} error(s)."
    elif isinstance(exception, InvalidGraph):
        return f"❌ Graph structure is invalid: {exception.issue}"
    else:
        return f"❌ Error: {exception.message}"


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the exceptions module."""
    print("=" * 80)
    print("TESTING EXCEPTIONS MODULE")
    print("=" * 80)
    
    # Test 1: Base exception
    print("\n1. Testing GraphError (base)...")
    try:
        raise GraphError("Test error", {'key': 'value'})
    except GraphError as e:
        print(f"✓ Caught GraphError: {e}")
        print(f"  Message: {e.message}")
        print(f"  Details: {e.details}")
    
    # Test 2: NodeNotFound
    print("\n2. Testing NodeNotFound...")
    try:
        raise NodeNotFound(999)
    except NodeNotFound as e:
        print(f"✓ Caught NodeNotFound: {e}")
        print(f"  Node ID: {e.node_id}")
        assert e.node_id == 999
    
    # Test 3: DuplicateNode
    print("\n3. Testing DuplicateNode...")
    try:
        raise DuplicateNode(1)
    except DuplicateNode as e:
        print(f"✓ Caught DuplicateNode: {e}")
        print(f"  Node ID: {e.node_id}")
    
    # Test 4: EdgeNotFound
    print("\n4. Testing EdgeNotFound...")
    try:
        raise EdgeNotFound(1, 99)
    except EdgeNotFound as e:
        print(f"✓ Caught EdgeNotFound: {e}")
        print(f"  Source: {e.source}, Destination: {e.destination}")
    
    # Test 5: DuplicateEdge
    print("\n5. Testing DuplicateEdge...")
    try:
        raise DuplicateEdge(1, 2)
    except DuplicateEdge as e:
        print(f"✓ Caught DuplicateEdge: {e}")
    
    # Test 6: InvalidCSV
    print("\n6. Testing InvalidCSV...")
    try:
        raise InvalidCSV(
            file_path="data/nodes.csv",
            issue="Missing required columns",
            missing_columns=['latitude', 'longitude']
        )
    except InvalidCSV as e:
        print(f"✓ Caught InvalidCSV: {e}")
        print(f"  File: {e.file_path}")
        print(f"  Issue: {e.issue}")
        print(f"  Missing columns: {e.missing_columns}")
    
    # Test 7: ValidationError
    print("\n7. Testing ValidationError...")
    try:
        raise ValidationError(
            errors=["Duplicate node IDs", "Invalid coordinates"],
            entity_type="nodes"
        )
    except ValidationError as e:
        print(f"✓ Caught ValidationError: {e}")
        print(f"  Errors: {e.errors}")
        print(f"  Entity type: {e.entity_type}")
    
    # Test 8: InvalidGraph
    print("\n8. Testing InvalidGraph...")
    try:
        raise InvalidGraph(
            issue="Graph has 3 disconnected components",
            details_dict={'num_components': 3}
        )
    except InvalidGraph as e:
        print(f"✓ Caught InvalidGraph: {e}")
        print(f"  Issue: {e.issue}")
    
    # Test 9: PathNotFound
    print("\n9. Testing PathNotFound...")
    try:
        raise PathNotFound(1, 999, algorithm="BFS")
    except PathNotFound as e:
        print(f"✓ Caught PathNotFound: {e}")
        print(f"  Start: {e.start_node}, Goal: {e.goal_node}")
        print(f"  Algorithm: {e.algorithm}")
    
    # Test 10: Exception hierarchy
    print("\n10. Testing exception hierarchy...")
    try:
        raise NodeNotFound(999)
    except NodeError as e:
        print(f"✓ Caught as NodeError: {e}")
    except GraphError as e:
        print(f"✗ Should have been caught as NodeError first")
    
    try:
        raise NodeNotFound(999)
    except GraphError as e:
        print(f"✓ NodeNotFound is also a GraphError: {e}")
    
    try:
        raise EdgeNotFound(1, 2)
    except GraphError as e:
        print(f"✓ EdgeNotFound is also a GraphError: {e}")
    
    # Test 11: format_exception_for_user
    print("\n11. Testing format_exception_for_user...")
    exceptions_to_test = [
        NodeNotFound(999),
        EdgeNotFound(1, 99),
        PathNotFound(1, 999, "BFS"),
        InvalidCSV("test.csv", "Missing columns"),
        ValidationError(["Error 1", "Error 2"]),
        InvalidGraph("Disconnected")
    ]
    
    for exc in exceptions_to_test:
        user_msg = format_exception_for_user(exc)
        print(f"  {type(exc).__name__}: {user_msg}")
    
    # Test 12: Exception hierarchy display
    print("\n12. Exception hierarchy:")
    hierarchy = get_exception_hierarchy()
    for base, subclasses in hierarchy.items():
        print(f"  {base}")
        for subclass, children in subclasses.items():
            print(f"    ├── {subclass}")
            for child in children:
                print(f"    │   └── {child}")
    
    print("\n" + "=" * 80)
    print("✓ ALL EXCEPTION TESTS PASSED")
    print("=" * 80)