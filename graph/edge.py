"""
Edge Module

This module defines the Edge class, which represents a road segment connecting
two locations in the road network graph. Each edge contains geographic, traffic,
and cost information for route optimization.

The Edge class is used by:
- Graph class (for storage and retrieval)
- Graph loader (for CSV parsing)
- Search algorithms (for cost calculation and path finding)
- Traffic simulation (for dynamic updates)

Edge attributes support multiple optimization criteria:
- Physical distance (meters)
- Travel time (minutes)
- Traffic congestion (1-5 scale)
- Risk factors (0-3 scale)
- Total cost (weighted combination)

Author: AI Course Project Team
Version: 2.0.0 (Phase 3 - Graph Engine)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
import math


@dataclass
class Edge:
    """
    Represents a road segment connecting two locations in the network.
    
    An Edge contains all information needed for route optimization:
    physical distance, travel time, traffic conditions, risk factors,
    and calculated costs.
    
    Attributes:
        edge_id: Unique integer identifier for this edge.
                 Used for tracking and debugging.
        source: ID of the source node (starting point of the road segment).
                Must match a valid node_id in the graph.
        destination: ID of the destination node (ending point of the road segment).
                     Must match a valid node_id in the graph.
        distance: Physical road distance in meters.
                  Used for distance-based optimization.
        travel_time: Estimated travel time in minutes.
                     Calculated from distance, speed_limit, and congestion.
                     Used for time-based optimization.
        speed_limit: Speed limit in km/h.
                     Based on road type and local regulations.
        road_type: Type of road (primary, secondary, trunk, residential, etc.).
                   Used for visualization and vehicle restrictions.
        direction: Road direction ("one_way" or "two_way").
                   Determines if edge can be traversed in reverse.
        congestion_level: Traffic congestion level (1=free flow, 5=severe).
                          Affects travel time and route preference.
        risk_level: Risk factor (0=very safe, 3=high risk).
                    Includes flooding, construction, accident-prone areas.
        total_cost: Calculated multi-criteria cost for optimization.
                    Weighted combination of distance, time, congestion, and risk.
    
    Example:
        >>> edge = Edge(
        ...     edge_id=1,
        ...     source=1,
        ...     destination=3,
        ...     distance=1250.5,
        ...     travel_time=5.2,
        ...     speed_limit=40,
        ...     road_type="primary",
        ...     direction="two_way",
        ...     congestion_level=3,
        ...     risk_level=1,
        ...     total_cost=15.8
        ... )
        >>> print(edge.distance)
        1250.5
        >>> print(edge.get_cost('time'))
        5.2
    """
    
    edge_id: int
    source: int
    destination: int
    distance: float
    travel_time: float
    speed_limit: int
    road_type: str
    direction: str
    congestion_level: int
    risk_level: int
    total_cost: float
    
    def __post_init__(self):
        """
        Validate edge attributes after initialization.
        
        This method ensures that all edge attributes have valid values
        before the object is used in the graph.
        
        Raises:
            ValueError: If any attribute is invalid
            TypeError: If any attribute has wrong type
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Type validation
        if not isinstance(self.edge_id, int):
            raise TypeError(f"edge_id must be int, got {type(self.edge_id)}")
        if not isinstance(self.source, int):
            raise TypeError(f"source must be int, got {type(self.source)}")
        if not isinstance(self.destination, int):
            raise TypeError(f"destination must be int, got {type(self.destination)}")
        if not isinstance(self.distance, (int, float)):
            raise TypeError(f"distance must be numeric, got {type(self.distance)}")
        if not isinstance(self.travel_time, (int, float)):
            raise TypeError(f"travel_time must be numeric, got {type(self.travel_time)}")
        if not isinstance(self.speed_limit, int):
            raise TypeError(f"speed_limit must be int, got {type(self.speed_limit)}")
        if not isinstance(self.road_type, str):
            raise TypeError(f"road_type must be str, got {type(self.road_type)}")
        if not isinstance(self.direction, str):
            raise TypeError(f"direction must be str, got {type(self.direction)}")
        if not isinstance(self.congestion_level, int):
            raise TypeError(f"congestion_level must be int, got {type(self.congestion_level)}")
        if not isinstance(self.risk_level, int):
            raise TypeError(f"risk_level must be int, got {type(self.risk_level)}")
        if not isinstance(self.total_cost, (int, float)):
            raise TypeError(f"total_cost must be numeric, got {type(self.total_cost)}")
        
        # Range validation
        if self.distance <= 0:
            raise ValueError(f"distance must be positive, got {self.distance}")
        if self.travel_time <= 0:
            raise ValueError(f"travel_time must be positive, got {self.travel_time}")
        if self.speed_limit <= 0:
            raise ValueError(f"speed_limit must be positive, got {self.speed_limit}")
        if self.congestion_level < 1 or self.congestion_level > 5:
            raise ValueError(f"congestion_level must be 1-5, got {self.congestion_level}")
        if self.risk_level < 0 or self.risk_level > 3:
            raise ValueError(f"risk_level must be 0-3, got {self.risk_level}")
        if self.total_cost < 0:
            raise ValueError(f"total_cost must be non-negative, got {self.total_cost}")
        
        # Direction validation
        if self.direction not in ["one_way", "two_way"]:
            raise ValueError(f"direction must be 'one_way' or 'two_way', got {self.direction}")
        
        # Source != destination (no self-loops)
        if self.source == self.destination:
            raise ValueError(f"source and destination must be different (no self-loops)")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert edge to dictionary for CSV export or JSON serialization.
        
        Returns:
            Dictionary with all edge attributes
            
        Example:
            >>> edge = Edge(1, 1, 3, 1250.5, 5.2, 40, "primary", "two_way", 3, 1, 15.8)
            >>> d = edge.to_dict()
            >>> d['distance']
            1250.5
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """
        Create an Edge from a dictionary (e.g., loaded from CSV).
        
        Args:
            data: Dictionary containing edge attributes
            
        Returns:
            New Edge instance
            
        Raises:
            KeyError: If required keys are missing
            ValueError: If values are invalid
            
        Example:
            >>> data = {'edge_id': 1, 'source': 1, 'destination': 3,
            ...         'distance': 1250.5, 'travel_time': 5.2, 'speed_limit': 40,
            ...         'road_type': 'primary', 'direction': 'two_way',
            ...         'congestion_level': 3, 'risk_level': 1, 'total_cost': 15.8}
            >>> edge = Edge.from_dict(data)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Type conversion (CSV loads everything as strings)
        data['edge_id'] = int(data['edge_id'])
        data['source'] = int(data['source'])
        data['destination'] = int(data['destination'])
        data['distance'] = float(data['distance'])
        data['travel_time'] = float(data['travel_time'])
        data['speed_limit'] = int(data['speed_limit'])
        data['congestion_level'] = int(data['congestion_level'])
        data['risk_level'] = int(data['risk_level'])
        data['total_cost'] = float(data['total_cost'])
        
        return cls(**data)
    
    def get_cost(self, metric: str = 'total_cost') -> float:
        """
        Get the cost value for a specific optimization metric.
        
        This method allows algorithms to choose which metric to optimize:
        - 'distance': Optimize for shortest physical distance
        - 'travel_time': Optimize for fastest travel time
        - 'congestion': Optimize for least congestion
        - 'risk': Optimize for lowest risk
        - 'total_cost': Optimize for weighted multi-criteria cost (default)
        
        Args:
            metric: The cost metric to retrieve
            
        Returns:
            Cost value for the specified metric
            
        Raises:
            ValueError: If metric is not recognized
            
        Example:
            >>> edge = Edge(1, 1, 3, 1250.5, 5.2, 40, "primary", "two_way", 3, 1, 15.8)
            >>> edge.get_cost('distance')
            1250.5
            >>> edge.get_cost('travel_time')
            5.2
            >>> edge.get_cost('total_cost')
            15.8
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        cost_metrics = {
            'distance': self.distance,
            'travel_time': self.travel_time,
            'congestion': self.congestion_level,
            'risk': self.risk_level,
            'total_cost': self.total_cost
        }
        
        if metric not in cost_metrics:
            raise ValueError(f"Unknown metric '{metric}'. Valid metrics: {list(cost_metrics.keys())}")
        
        return cost_metrics[metric]
    
    def get_average_speed(self) -> float:
        """
        Calculate average speed considering congestion.
        
        Returns:
            Average speed in km/h, adjusted for traffic conditions
            
        Example:
            >>> edge = Edge(1, 1, 3, 1250.5, 5.2, 40, "primary", "two_way", 3, 1, 15.8)
            >>> speed = edge.get_average_speed()
            >>> print(f"Average speed: {speed:.1f} km/h")
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Congestion reduces speed
        congestion_factor = {
            1: 1.0,   # Free flow: 100% of speed limit
            2: 0.8,   # Light traffic: 80%
            3: 0.6,   # Moderate: 60%
            4: 0.4,   # Heavy: 40%
            5: 0.2    # Severe: 20%
        }
        
        factor = congestion_factor.get(self.congestion_level, 0.5)
        return self.speed_limit * factor
    
    def is_one_way(self) -> bool:
        """
        Check if the edge is one-way.
        
        Returns:
            True if edge is one-way, False if two-way
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return self.direction == "one_way"
    
    def can_traverse_reverse(self) -> bool:
        """
        Check if the edge can be traversed in reverse direction.
        
        Returns:
            True if edge is two-way, False if one-way
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return self.direction == "two_way"
    
    def __str__(self) -> str:
        """
        Human-readable string representation.
        
        Returns:
            Formatted string with edge information
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return f"Edge({self.edge_id}: {self.source} → {self.destination}, {self.distance:.0f}m)"
    
    def __repr__(self) -> str:
        """
        Detailed string representation for debugging.
        
        Returns:
            String with all attributes
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return (f"Edge(edge_id={self.edge_id}, source={self.source}, "
                f"destination={self.destination}, distance={self.distance:.1f}m, "
                f"time={self.travel_time:.1f}min, cost={self.total_cost:.2f})")
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality based on edge_id.
        
        Args:
            other: Another object to compare with
            
        Returns:
            True if both edges have the same edge_id
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        if not isinstance(other, Edge):
            return False
        return self.edge_id == other.edge_id
    
    def __hash__(self) -> int:
        """
        Hash based on edge_id for use in sets and dicts.
        
        Returns:
            Hash value
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        return hash(self.edge_id)


# ============================================================================
# TRAFFIC SIMULATOR
# ============================================================================

class TrafficSimulator:
    """
    Simulates traffic conditions for road segments.
    
    This class provides methods to calculate travel time, congestion,
    risk, and total cost based on road characteristics and location types.
    It's used during graph construction to populate edge attributes.
    
    The simulator uses realistic assumptions for Vietnamese urban traffic:
    - Road types determine base speed limits
    - Location types affect congestion (markets are busier)
    - Districts have different risk profiles (flooding, accidents)
    """
    
    # Base speed limits by road type (km/h)
    SPEED_LIMITS = {
        'motorway': 80,
        'trunk': 60,
        'primary': 50,
        'secondary': 40,
        'tertiary': 30,
        'residential': 25,
        'unclassified': 30,
        'service': 20
    }
    
    # Base congestion by road type (1-5)
    BASE_CONGESTION = {
        'motorway': 2,
        'trunk': 2,
        'primary': 2,
        'secondary': 2,
        'tertiary': 2,
        'residential': 1,
        'unclassified': 2,
        'service': 1
    }
    
    # Congestion modifiers by location type
    LOCATION_CONGESTION_MODIFIERS = {
        'market': 1,
        'hospital': 1,
        'university': 1,
        'shopping': 1,
        'office': 1,
        'warehouse': 0,
        'landmark': 1,
        'park': 0,
        'residential': 0,
        'event_venue': 1
    }
    
    # Risk factors by district (flood-prone, accident-prone, etc.)
    DISTRICT_RISK = {
        'District 1': 0,
        'District 3': 0,
        'District 5': 1,
        'District 6': 1,
        'District 7': 0,
        'District 10': 1,
        'District 11': 1,
        'Tan Binh': 0,
        'Binh Thanh': 1,
        'Phu Nhuan': 0,
        'Tan Phu': 1
    }
    
    @classmethod
    def calculate_travel_time(
        cls,
        distance: float,
        speed_limit: int,
        congestion_level: int
    ) -> float:
        """
        Calculate travel time considering distance, speed, and congestion.
        
        Args:
            distance: Distance in meters
            speed_limit: Speed limit in km/h
            congestion_level: Congestion level (1-5)
            
        Returns:
            Travel time in minutes
            
        Formula:
            effective_speed = speed_limit × congestion_factor
            time_hours = distance / 1000 / effective_speed
            time_minutes = time_hours × 60
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Congestion factor (how much speed is reduced)
        congestion_factor = {
            1: 1.0,   # Free flow: 100% of speed limit
            2: 0.8,   # Light traffic: 80%
            3: 0.6,   # Moderate: 60%
            4: 0.4,   # Heavy: 40%
            5: 0.2    # Severe: 20%
        }
        
        factor = congestion_factor.get(congestion_level, 0.5)
        effective_speed = speed_limit * factor  # km/h
        
        # Convert to minutes
        time_hours = (distance / 1000) / effective_speed
        time_minutes = time_hours * 60
        
        return round(time_minutes, 2)
    
    @classmethod
    def simulate_congestion(
        cls,
        road_type: str,
        source_type: str = '',
        destination_type: str = ''
    ) -> int:
        """
        Simulate congestion level based on road and location types.
        
        Args:
            road_type: Type of road
            source_type: Type of source location
            destination_type: Type of destination location
            
        Returns:
            Congestion level (1-5)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Base congestion from road type
        base = cls.BASE_CONGESTION.get(road_type, 2)
        
        # Add modifiers from location types
        source_modifier = cls.LOCATION_CONGESTION_MODIFIERS.get(source_type, 0)
        dest_modifier = cls.LOCATION_CONGESTION_MODIFIERS.get(destination_type, 0)
        
        # Total congestion
        total = base + source_modifier + dest_modifier
        
        # Clamp to 1-5 range
        return max(1, min(5, total))
    
    @classmethod
    def simulate_risk(
        cls,
        source_district: str,
        destination_district: str,
        road_type: str
    ) -> int:
        """
        Simulate risk level based on districts and road type.
        
        Args:
            source_district: District of source node
            destination_district: District of destination node
            road_type: Type of road
            
        Returns:
            Risk level (0-3)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Base risk from districts
        source_risk = cls.DISTRICT_RISK.get(source_district, 1)
        dest_risk = cls.DISTRICT_RISK.get(destination_district, 1)
        
        # Average risk
        base_risk = (source_risk + dest_risk) / 2
        
        # Road type modifier
        road_modifier = 0
        if road_type in ['residential', 'service', 'secondary']:
            road_modifier = 0  # Small roads are safer
        elif road_type in ['motorway', 'trunk']:
            road_modifier = 1  # Major highways have higher risk
        
        # Total risk
        total = base_risk + road_modifier
        
        # Clamp to 0-3 range
        return max(0, min(3, round(total)))
    
    @classmethod
    def calculate_total_cost(
        cls,
        distance: float,
        travel_time: float,
        congestion_level: int,
        risk_level: int,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate multi-criteria total cost using weighted sum.
        
        Args:
            distance: Distance in meters
            travel_time: Travel time in minutes
            congestion_level: Congestion level (1-5)
            risk_level: Risk level (0-3)
            weights: Dictionary of weights for each factor
            
        Returns:
            Total cost (normalized and weighted)
            
        Formula:
            total_cost = w1 × norm_distance + 
                        w2 × norm_time + 
                        w3 × norm_congestion + 
                        w4 × norm_risk
            
        Normalization:
            - distance: distance / 1000 (km)
            - time: travel_time (minutes)
            - congestion: congestion_level / 5 (0.2 to 1.0)
            - risk: risk_level / 3 (0 to 1.0)
            
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        # Default weights (from lab requirements)
        if weights is None:
            weights = {
                'distance': 0.3,
                'time': 0.4,
                'congestion': 0.2,
                'risk': 0.1
            }
        
        # Normalize each factor
        norm_distance = distance / 1000  # Convert to km
        norm_time = travel_time
        norm_congestion = congestion_level / 5.0  # 0.2 to 1.0
        norm_risk = risk_level / 3.0  # 0 to 1.0
        
        # Weighted sum
        total_cost = (
            weights['distance'] * norm_distance +
            weights['time'] * norm_time +
            weights['congestion'] * norm_congestion +
            weights['risk'] * norm_risk
        )
        
        return round(total_cost, 2)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_edge_from_dict(data: Dict[str, Any]) -> Edge:
    """
    Create an Edge from a dictionary with type conversion.
    
    This is a convenience function that handles type conversions
    when loading from CSV or other text-based formats.
    
    Args:
        data: Dictionary with edge attributes (may have string values)
        
    Returns:
        New Edge instance
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    return Edge.from_dict(data)


def validate_edges(edges: List[Edge]) -> Tuple[bool, List[str]]:
    """
    Validate a list of edges for consistency and correctness.
    
    Checks:
    - No duplicate edge_ids
    - All distances are positive
    - All travel times are positive
    - All costs are non-negative
    
    Args:
        edges: List of Edge objects
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        
    Time Complexity: O(n) where n is number of edges
    Space Complexity: O(n) for storing errors
    """
    errors = []
    
    # Check for duplicate IDs
    ids = [e.edge_id for e in edges]
    if len(ids) != len(set(ids)):
        duplicates = [id for id in ids if ids.count(id) > 1]
        errors.append(f"Duplicate edge IDs found: {set(duplicates)}")
    
    # Validate each edge
    for edge in edges:
        if edge.distance <= 0:
            errors.append(f"Edge {edge.edge_id} has non-positive distance: {edge.distance}")
        if edge.travel_time <= 0:
            errors.append(f"Edge {edge.edge_id} has non-positive travel_time: {edge.travel_time}")
        if edge.total_cost < 0:
            errors.append(f"Edge {edge.edge_id} has negative total_cost: {edge.total_cost}")
    
    is_valid = len(errors) == 0
    return (is_valid, errors)

def _infer_road_type(
    distance: float,
    source_type: str,
    destination_type: str,
    source_district: str,
    destination_district: str
) -> str:
    """
    Infer road type based on edge characteristics.
    
    Since we didn't preserve road types from OSM data, we infer them
    based on distance, location types, and districts.
    
    Args:
        distance: Edge distance in meters
        source_type: Type of source location
        destination_type: Type of destination location
        source_district: District of source location
        destination_district: District of destination location
        
    Returns:
        Inferred road type string
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    # Special case: Airport connections are major roads
    if 'airport' in source_type.lower() or 'airport' in destination_type.lower():
        if distance > 2000:
            return 'trunk'
        return 'primary'
    
    # Special case: Very long distances are major roads
    if distance > 3000:
        return 'trunk'
    
    # Special case: Landmark to landmark connections
    if source_type == 'landmark' and destination_type == 'landmark':
        if distance > 1500:
            return 'trunk'
        return 'primary'
    
    # Special case: Market areas have narrower roads
    if source_type == 'market' or destination_type == 'market':
        if distance < 1000:
            return 'secondary'
        return 'primary'
    
    # Special case: Residential areas
    if source_type == 'residential' or destination_type == 'residential':
        if distance < 800:
            return 'residential'
        return 'secondary'
    
    # Distance-based inference for general cases
    if distance < 500:
        return 'residential'
    elif distance < 1000:
        return 'secondary'
    elif distance < 2500:
        return 'primary'
    else:
        return 'trunk'


def create_edge_from_graph_data(
    edge_id: int,
    source: int,
    destination: int,
    graph_edge_data: Dict[str, Any],
    source_node_data: Dict[str, Any],
    destination_node_data: Dict[str, Any]
) -> Edge:
    """
    Create an Edge from graph edge and node attributes.
    
    This function:
    1. Extracts distance from graph
    2. Infers road type from edge characteristics
    3. Determines speed limit based on road type
    4. Simulates traffic conditions (congestion, risk)
    5. Calculates travel time and total cost
    
    It's used by the CSV exporter (Phase 2) to convert graph data to Edge objects.
    
    Args:
        edge_id: Unique edge identifier
        source: Source node ID
        destination: Destination node ID
        graph_edge_data: Edge attributes from NetworkX
        source_node_data: Source node attributes (type, district)
        destination_node_data: Destination node attributes (type, district)
        
    Returns:
        New Edge instance with all calculated attributes
        
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    # Extract distance
    distance = float(graph_edge_data.get('distance', 0))
    
    # Get location types and districts
    source_type = source_node_data.get('type', '')
    dest_type = destination_node_data.get('type', '')
    source_district = source_node_data.get('district', '')
    dest_district = destination_node_data.get('district', '')
    
    # Infer road type
    road_type = _infer_road_type(
        distance=distance,
        source_type=source_type,
        destination_type=dest_type,
        source_district=source_district,
        destination_district=dest_district
    )
    
    # Get speed limit based on road type
    speed_limit = TrafficSimulator.SPEED_LIMITS.get(road_type, 40)
    
    # Direction (default to two_way)
    direction = "two_way"
    
    # Simulate traffic conditions
    congestion_level = TrafficSimulator.simulate_congestion(
        road_type, source_type, dest_type
    )
    
    risk_level = TrafficSimulator.simulate_risk(
        source_district, dest_district, road_type
    )
    
    # Calculate travel time
    travel_time = TrafficSimulator.calculate_travel_time(
        distance, speed_limit, congestion_level
    )
    
    # Calculate total cost
    total_cost = TrafficSimulator.calculate_total_cost(
        distance, travel_time, congestion_level, risk_level
    )
    
    return Edge(
        edge_id=edge_id,
        source=source,
        destination=destination,
        distance=distance,
        travel_time=travel_time,
        speed_limit=speed_limit,
        road_type=road_type,
        direction=direction,
        congestion_level=congestion_level,
        risk_level=risk_level,
        total_cost=total_cost
    )

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the Edge class and traffic simulation."""
    print("=" * 70)
    print("TESTING EDGE CLASS AND TRAFFIC SIMULATION")
    print("=" * 70)
    
    # Test 1: Create an edge
    print("\n1. Creating an edge...")
    edge = Edge(
        edge_id=1,
        source=1,
        destination=3,
        distance=1250.5,
        travel_time=5.2,
        speed_limit=40,
        road_type="primary",
        direction="two_way",
        congestion_level=3,
        risk_level=1,
        total_cost=15.8
    )
    print(f"✓ Created: {edge}")
    
    # Test 2: Get cost metrics
    print("\n2. Testing get_cost()...")
    print(f"  Distance: {edge.get_cost('distance')}m")
    print(f"  Travel time: {edge.get_cost('travel_time')} min")
    print(f"  Congestion: {edge.get_cost('congestion')}")
    print(f"  Risk: {edge.get_cost('risk')}")
    print(f"  Total cost: {edge.get_cost('total_cost')}")
    
    # Test 3: Traffic simulation
    print("\n3. Testing traffic simulation...")
    
    # Calculate travel time
    time = TrafficSimulator.calculate_travel_time(
        distance=1250.5,
        speed_limit=40,
        congestion_level=3
    )
    print(f"✓ Travel time (1250m, 40km/h, congestion=3): {time:.2f} minutes")
    
    # Simulate congestion
    congestion = TrafficSimulator.simulate_congestion(
        road_type="primary",
        source_type="market",
        destination_type="office"
    )
    print(f"✓ Simulated congestion (primary road, market→office): {congestion}")
    
    # Simulate risk
    risk = TrafficSimulator.simulate_risk(
        source_district="District 1",
        destination_district="Binh Thanh",
        road_type="primary"
    )
    print(f"✓ Simulated risk (District 1 → Binh Thanh, primary): {risk}")
    
    # Calculate total cost
    cost = TrafficSimulator.calculate_total_cost(
        distance=1250.5,
        travel_time=5.2,
        congestion_level=3,
        risk_level=1
    )
    print(f"✓ Total cost: {cost:.2f}")
    
    # Test 4: Average speed
    print("\n4. Testing average speed...")
    avg_speed = edge.get_average_speed()
    print(f"✓ Average speed (congestion={edge.congestion_level}): {avg_speed:.1f} km/h")
    
    # Test 5: Direction methods
    print("\n5. Testing direction methods...")
    print(f"  Is one-way: {edge.is_one_way()}")
    print(f"  Can traverse reverse: {edge.can_traverse_reverse()}")
    
    # Test 6: Serialization
    print("\n6. Testing serialization...")
    edge_dict = edge.to_dict()
    print(f"✓ Converted to dict with {len(edge_dict)} keys")
    
    edge2 = Edge.from_dict(edge_dict)
    print(f"✓ Created from dict: {edge2}")
    assert edge == edge2
    print("✓ Round-trip successful")
    
    # Test 7: Validation
    print("\n7. Testing validation...")
    edges = [edge]
    is_valid, errors = validate_edges(edges)
    print(f"✓ Validation: {is_valid}")
    
    # Test 8: Invalid edge
    print("\n8. Testing invalid edge creation...")
    try:
        invalid_edge = Edge(
            edge_id=99,
            source=1,
            destination=3,
            distance=-100,  # Invalid!
            travel_time=5.2,
            speed_limit=40,
            road_type="primary",
            direction="two_way",
            congestion_level=3,
            risk_level=1,
            total_cost=15.8
        )
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("\n" + "=" * 70)
    print("✓ ALL EDGE TESTS PASSED")
    print("=" * 70)