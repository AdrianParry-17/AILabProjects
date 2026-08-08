# core

The reusable search framework every algorithm builds on.

```
search_algorithm.py  # SearchAlgorithm ABC, ALGORITHM_REGISTRY, run_algorithm()
search_result.py     # SearchResult + SearchStep (uniform output model)
search_event.py      # SearchEvent / SearchEventKind (animation/history stream)
search_history.py    # SearchHistory (bounded in-memory run log)
search_metrics.py    # SearchMetrics summary derived from a SearchResult
```

`core` imports from `shared` only. `algorithms/` implements `SearchAlgorithm`
subclasses and registers them; `visualization/` and `ui/` call `run_algorithm()`.
