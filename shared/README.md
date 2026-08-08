# shared

Generic, dependency-free utilities shared by every layer.

```
constants.py    # generic numeric constants
enums.py        # Direction, TrafficCondition, AlgorithmName
exceptions.py   # project-wide exception hierarchy (CONVENTION.md § 6.1)
logger.py       # get_logger() / configure_cli_logging()
helpers.py      # haversine_m(), stable_fraction()
validators.py   # ensure_schema_version(), ensure_unique()
types.py        # NodeLike, EdgeLike, GraphLike, LatLon, Polyline, NodeId
```

This is the **lowest layer**: it imports only the standard library. Nothing else
may import upward to it from here.
