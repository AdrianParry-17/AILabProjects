# config

Centralized, single-source configuration for the whole project.

```
paths.py      # filesystem layout (RAW_DIR, ROAD_GRAPH_PATH, DELIVERY_GRAPH_PATH, ...)
defaults.py   # build/algorithm tuning (BBOX, POI_FILTER, DEFAULT_COUNTS, CostWeights, ...)
settings.py   # app settings (PROJECT_NAME, SCHEMA_VERSION)
```

`config` imports from `shared` only. Nothing in this package contains logic — just
values other layers resolve against.
