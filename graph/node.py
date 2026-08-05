"""
Node Module

This module defines the Node class, which represents a location or intersection
in the road network graph. Each node contains geographic coordinates, metadata,
and methods for spatial calculations.

The Node class is a fundamental building block used by:
- Graph class (for storage and retrieval)
- Graph loader (for CSV parsing)
- Search algorithms (for path finding and heuristics)
- Visualization (for map display)

Author: AI Course Project Team
Version: 2.0.0 (Phase 3 - Graph Engine)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple
import math


@dataclass
class Node:
    """
    Represents a location or intersection in the road network.
    
    A Node is the fundamental unit of the graph. It contains geographic
    coordinates for map visualization, metadata for display purposes,
    and methods for spatial calculations.
    
    Attributes:
        node_id: Unique integer identifier for this node (1-25 for our project).
                 This is our internal ID used throughout the application.
        name: Human-readable name of the location (e.g., "Ben Thanh Market").
              Used for display in GUI and route explanations.
        latitude: Geographic latitude in decimal degrees (-90 to 90).
                  Used for map positioning and distance calculations.
        longitude: Geographic longitude in decimal degrees (-180 to 180).
                   Used for map positioning and distance calculations.
        district: Administrative district name (e.g., "District 1", "Tan Binh").
                  Used for grouping, filtering, and risk assessment.
        type: Category of location (warehouse, market, hospital, university, etc.).
              Used for traffic simulation and visualization styling.
        osm_id: Original OpenStreetMap node ID for traceability.
                Links back to real-world data source.
    
    Example:
        >>> node = Node(
        ...     node_id=3,
        ...     name="Ben Thanh Market",
        ...     latitude=10.7725,
        ...     longitude=106.6980,
        ...     district="District 1",
        ...     type="market",
        ...     osm_id=411926070
        ... )
        >>> print(node.name)
        Ben Thanh Market
        >>> print(node.get_coordinates())
        (10.7725, 106.698)
    """
    
    node_id: int
    name: str
    latitude: float
    longitude: float
    district: str
    type: str
    osm_id: int
    
    def __post_init__(self):
        """
        Validate node attributes after initialization.
        
        This method is automatically called by the dataclass __init__.
        It ensures that all attributes have valid values before the object
        is used.
        
        Raises:
            ValueError: If any attribute is invalid
            TypeError: If any attribute has wrong type
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Type validation
        if not isinstance(self.node_id, int):
            raise TypeError(f"node_id must be int, got {type(self.node_id)}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.latitude, (int, float)):
            raise TypeError(f"latitude must be numeric, got {type(self.latitude)}")
        if not isinstance(self.longitude, (int, float)):
            raise TypeError(f"longitude must be numeric, got {type(self.longitude)}")
        if not isinstance(self.district, str) or not self.district.strip():
            raise ValueError("district must be a non-empty string")
        if not isinstance(self.type, str) or not self.type.strip():
            raise ValueError("type must be a non-empty string")
        if not isinstance(self.osm_id, int):
            raise TypeError(f"osm_id must be int, got {type(self.osm_id)}")
        
        # Range validation
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"longitude must be between -180 and 180, got {self.longitude}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary for CSV export or JSON serialization.
        
        Returns:
            Dictionary with all node attributes
            
        Example:
            >>> node = Node(1, "Warehouse", 10.8, 106.6, "Tan Binh", "warehouse", 123)
            >>> d = node.to_dict()
            >>> d['name']
            'Warehouse'
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        Create a Node from a dictionary (e.g., loaded from CSV).
        
        Args:
            data: Dictionary containing node attributes
            
        Returns:
            New Node instance
            
        Raises:
            KeyError: If required keys are missing
            ValueError: If values are invalid
            
        Example:
            >>> data = {'node_id': 1, 'name': 'Warehouse', 'latitude': 10.8,
            ...         'longitude': 106.6, 'district': 'Tan Binh',
            ...         'type': 'warehouse', 'osm_id': 123}
            >>> node = Node.from_dict(data)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Type conversion (CSV loads everything as strings)
        data['node_id'] = int(data['node_id'])
        data['latitude'] = float(data['latitude'])
        data['longitude'] = float(data['longitude'])
        data['osm_id'] = int(data['osm_id'])
        
        return cls(**data)
    
    def distance_to(self, other: 'Node') -> float:
        """
        Calculate the great-circle distance to another node using Haversine formula.
        
        The Haversine formula calculates the shortest distance between two points
        on a sphere given their latitudes and longitudes.
        
        Args:
            other: Another Node to calculate distance to
            
        Returns:
            Distance in meters
            
        Formula:
            a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
            c = 2 × atan2(√a, √(1-a))
            d = R × c
            
        where R = 6,371,000 meters (Earth's radius)
        
        Example:
            >>> n1 = Node(1, "A", 10.7725, 106.6980, "D1", "market", 1)
            >>> n2 = Node(2, "B", 10.7795, 106.6995, "D1", "landmark", 2)
            >>> distance = n1.distance_to(n2)
            >>> print(f"Distance: {distance:.2f}m")
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_coordinates(self) -> Tuple[float, float]:
        """
        Get the geographic coordinates as a tuple.
        
        Returns:
            Tuple of (latitude, longitude)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return (self.latitude, self.longitude)
    
    def is_valid_for_hcmc(self) -> bool:
        """
        Check if the node's coordinates are within Ho Chi Minh City bounds.
        
        HCMC approximate bounds:
        - Latitude: 10.38 to 11.15
        - Longitude: 106.36 to 107.01
        
        Returns:
            True if coordinates are within HCMC, False otherwise
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        hcmc_lat_min, hcmc_lat_max = 10.38, 11.15
        hcmc_lon_min, hcmc_lon_max = 106.36, 107.01
        
        return (hcmc_lat_min <= self.latitude <= hcmc_lat_max and
                hcmc_lon_min <= self.longitude <= hcmc_lon_max)
    
    def __str__(self) -> str:
        """
        Human-readable string representation.
        
        Returns:
            Formatted string with node information
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return f"Node({self.node_id}: {self.name}, {self.district})"
    
    def __repr__(self) -> str:
        """
        Detailed string representation for debugging.
        
        Returns:
            String with all attributes
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return (f"Node(node_id={self.node_id}, name='{self.name}', "
                f"lat={self.latitude:.4f}, lon={self.longitude:.4f}, "
                f"district='{self.district}', type='{self.type}', "
                f"osm_id={self.osm_id})")
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality based on node_id.
        
        Args:
            other: Another object to compare with
            
        Returns:
            True if both nodes have the same node_id
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if not isinstance(other, Node):
            return False
        return self.node_id == other.node_id
    
    def __hash__(self) -> int:
        """
        Hash based on node_id for use in sets and dicts.
        
        Returns:
            Hash value
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return hash(self.node_id)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_node_from_dict(data: Dict[str, Any]) -> Node:
    """
    Create a Node from a dictionary with type conversion.
    
    This is a convenience function that handles type conversions
    when loading from CSV or other text-based formats.
    
    Args:
        data: Dictionary with node attributes (may have string values)
        
    Returns:
        New Node instance
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    return Node.from_dict(data)


def validate_nodes(nodes: list) -> Tuple[bool, list]:
    """
    Validate a list of nodes for consistency and correctness.
    
    Checks:
    - No duplicate node_ids
    - No duplicate names
    - All coordinates are valid
    - All nodes are within HCMC bounds
    - No missing required fields
    
    Args:
        nodes: List of Node objects
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        
    Time Complexity: O(n) where n is number of nodes
    Space Complexity: O(n) for storing errors
    """
    errors = []
    
    # Check for duplicate IDs
    ids = [n.node_id for n in nodes]
    if len(ids) != len(set(ids)):
        duplicates = [id for id in ids if ids.count(id) > 1]
        errors.append(f"Duplicate node IDs found: {set(duplicates)}")
    
    # Check for duplicate names
    names = [n.name for n in nodes]
    if len(names) != len(set(names)):
        duplicates = [name for name in names if names.count(name) > 1]
        errors.append(f"Duplicate node names found: {set(duplicates)}")
    
    # Validate each node
    for node in nodes:
        if not node.is_valid_for_hcmc():
            errors.append(
                f"Node {node.node_id} ({node.name}) coordinates "
                f"({node.latitude}, {node.longitude}) outside HCMC bounds"
            )
    
    is_valid = len(errors) == 0
    return (is_valid, errors)

def create_node_from_graph_data(
    node_id: int,
    graph_node_data: Dict[str, Any]
) -> Node:
    """
    Create a Node from graph node attributes (as stored in NetworkX).
    
    This function handles the conversion from NetworkX node attributes
    to our Node dataclass, including type conversions and defaults.
    It's used by the CSV exporter (Phase 2) to convert graph data to Node objects.
    
    Args:
        node_id: The node identifier
        graph_node_data: Dictionary of node attributes from NetworkX
        
    Returns:
        New Node instance
        
    Raises:
        ValueError: If required attributes are missing or invalid
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    # Extract attributes with defaults
    name = str(graph_node_data.get('name', f'Node_{node_id}'))
    
    # Handle coordinate conversion (may be strings from GraphML)
    try:
        latitude = float(graph_node_data.get('latitude', 0))
    except (ValueError, TypeError):
        raise ValueError(f"Invalid latitude for node {node_id}")
    
    try:
        longitude = float(graph_node_data.get('longitude', 0))
    except (ValueError, TypeError):
        raise ValueError(f"Invalid longitude for node {node_id}")
    
    district = str(graph_node_data.get('district', 'Unknown'))
    node_type = str(graph_node_data.get('type', 'unknown'))
    
    # Handle OSM ID (may be string from GraphML)
    try:
        osm_id = int(graph_node_data.get('osm_id', node_id))
    except (ValueError, TypeError):
        osm_id = node_id
    
    return Node(
        node_id=node_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        district=district,
        type=node_type,
        osm_id=osm_id
    )

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the Node class."""
    print("=" * 70)
    print("TESTING NODE CLASS")
    print("=" * 70)
    
    # Test 1: Create a node
    print("\n1. Creating a node...")
    node1 = Node(
        node_id=1,
        name="Warehouse (Main Hub)",
        latitude=10.8025,
        longitude=106.6545,
        district="Tan Binh",
        type="warehouse",
        osm_id=366423309
    )
    print(f"✓ Created: {node1}")
    print(f"  Repr: {repr(node1)}")
    
    # Test 2: Convert to dict
    print("\n2. Converting to dictionary...")
    node_dict = node1.to_dict()
    print(f"✓ Dictionary keys: {list(node_dict.keys())}")
    
    # Test 3: Create from dict
    print("\n3. Creating from dictionary...")
    node2 = Node.from_dict(node_dict)
    print(f"✓ Created: {node2}")
    assert node1 == node2, "Nodes should be equal"
    print("✓ Nodes are equal")
    
    # Test 4: Calculate distance
    print("\n4. Calculating distance...")
    node3 = Node(
        node_id=3,
        name="Ben Thanh Market",
        latitude=10.7725,
        longitude=106.6980,
        district="District 1",
        type="market",
        osm_id=411926070
    )
    distance = node1.distance_to(node3)
    print(f"✓ Distance from {node1.name} to {node3.name}: {distance:.2f}m")
    
    # Test 5: Validate HCMC bounds
    print("\n5. Validating HCMC bounds...")
    is_valid = node1.is_valid_for_hcmc()
    print(f"✓ {node1.name} is in HCMC: {is_valid}")
    
    # Test 6: Get coordinates
    print("\n6. Getting coordinates...")
    coords = node1.get_coordinates()
    print(f"✓ Coordinates: {coords}")
    
    # Test 7: Validation
    print("\n7. Testing validation...")
    nodes = [node1, node3]
    is_valid, errors = validate_nodes(nodes)
    print(f"✓ Validation result: {is_valid}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test 8: Invalid node
    print("\n8. Testing invalid node creation...")
    try:
        invalid_node = Node(
            node_id=99,
            name="Invalid",
            latitude=200,  # Invalid!
            longitude=106,
            district="Test",
            type="test",
            osm_id=1
        )
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("\n" + "=" * 70)
    print("✓ ALL NODE TESTS PASSED")
    print("=" * 70)