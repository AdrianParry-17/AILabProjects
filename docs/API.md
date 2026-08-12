# FastAPI Contract — `/api/v1`

Contract này mô tả backend v2.0.0 của **HCMC Delivery Route Lab**. API phục vụ việc học và so sánh thuật toán tìm kiếm trên snapshot đường phố trung tâm Thành phố Hồ Chí Minh; nó không phải dịch vụ traffic/navigation live và không xác nhận một cung đường hợp pháp cho xe máy hay bất kỳ loại phương tiện cụ thể nào.

## 1. Service URLs

| Resource | Development URL |
|---|---|
| API base | `http://127.0.0.1:8000/api/v1` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| OpenAPI JSON | `http://127.0.0.1:8000/api/v1/openapi.json` |
| React dev UI | `http://localhost:5173` |

Vite proxy `/api/*` sang backend trong cấu hình development. Các biến môi trường backend:

| Variable | Meaning |
|---|---|
| `ROUTING_DATASET_PATH` | override đường dẫn snapshot JSON đã chuẩn hóa |
| `CORS_ORIGINS` | danh sách exact origin, phân cách bằng dấu phẩy |

## 2. General conventions

- Media type là `application/json`.
- ID phân biệt hoa/thường.
- Request model là strict; field lạ bị từ chối bằng HTTP 422.
- GeoJSON dùng thứ tự `[longitude, latitude]`.
- Cost weight phải không âm, mỗi giá trị trong `[0,100]`, và tổng phải dương.
- Backend chuẩn hóa tỷ lệ weight; vì vậy `[1,2,3,4]` và `[10,20,30,40]` tương đương.
- Route/traffic output deterministic cho cùng code, dataset và request, ngoại trừ `request_id` và `runtime_ms`.
- `status=limit_reached` khác `status=unreachable`.
- UI objective như “Balanced”, “Shortest distance” và “Fastest ETA” là preset tạo `cost_weights`; API không nhận field `objective` hay `vehicle` giả.

### 2.1 Enum registry

```text
algorithms:
  bfs, dfs, ucs, dijkstra, astar, greedy_best_first,
  bidirectional_dijkstra, ida_star

heuristics:
  zero, haversine, travel_time, traffic_aware

scenarios:
  normal, morning_rush, evening_rush, heavy_rain, incident

multi-route methods:
  nearest_neighbor, held_karp, two_opt, simulated_annealing
```

`incident` nghĩa là kịch bản gián đoạn/đóng đường deterministic, không phải sự cố được lấy từ feed live.

### 2.2 Cost model

Request mặc định:

```json
{
  "distance": 0.25,
  "travel_time": 0.50,
  "traffic_delay": 0.20,
  "risk": 0.05
}
```

Sau khi chuẩn hóa weight, mỗi cung dùng:

```text
cost(e) = ŵ_distance × distance_km
        + ŵ_time     × travel_minutes
        + ŵ_delay    × delay_minutes
        + ŵ_risk     × (risk × distance_km)
```

`risk`, congestion, ETA, flood susceptibility và road disruption là dữ liệu/ước lượng giáo dục có provenance; không phải phép đo hiện trường.

## 3. Error envelope

Application error và validation error dùng một top-level envelope:

```json
{
  "error": {
    "code": "unknown_node",
    "message": "Unknown start node 'missing'",
    "details": {
      "role": "start",
      "node_id": "missing"
    }
  }
}
```

| HTTP | Typical code | Cause |
|---:|---|---|
| 422 | `validation_error` | enum/range/strict field sai; duplicate algorithm/stop; start nằm trong stops; Held–Karp >10 stop |
| 422 | `unknown_node` | start, goal hoặc stop không tồn tại |
| 422 | `multi_route_unreachable` | không có thứ tự hữu hạn ghé hết stop trong directed graph |
| 422 | `multi_route_failed` | optimizer không thể xử lý cấu hình đã qua HTTP validation |
| 503 | `service_unavailable` | engine/dataset chưa sẵn sàng |

Các code như `invalid_search_configuration`, `duplicate_start`, `duplicate_stops` và `too_many_stops` vẫn bảo vệ engine khi được gọi trực tiếp. Qua HTTP contract hiện tại, enum/model validator chặn các trường hợp tương ứng trước và trả `validation_error`.

Dataset load error làm application startup thất bại thay vì phục vụ graph một phần.

## 4. `GET /health`

Readiness của process và dataset hiện được nạp:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

```json
{
  "status": "ok",
  "service": "HCMC Delivery Route Lab API",
  "version": "2.0.0",
  "dataset_id": "hcmc-city-centre-delivery-osm-2026",
  "dataset_version": "2.0.0",
  "node_count": 1103,
  "directed_edge_count": 2279
}
```

Endpoint này không kiểm tra internet tile, live traffic hoặc tính hợp pháp của route ngoài đời.

## 5. `GET /metadata`

Trả registry để client không cần hard-code algorithm/scenario:

```text
api
dataset
graph
algorithms[]
heuristics[]
scenarios[]
multi_route_methods[]
defaults
trace_schema
```

Selected values của snapshot bundled:

```json
{
  "api": {
    "name": "HCMC Delivery Route Lab API",
    "version": "2.0.0",
    "contract_version": "2026-08-09"
  },
  "dataset": {
    "id": "hcmc-city-centre-delivery-osm-2026",
    "name": "Ho Chi Minh City Delivery Route Search Graph",
    "city": "Thành phố Hồ Chí Minh",
    "version": "2.0.0"
  },
  "graph": {
    "node_count": 1103,
    "directed_edge_count": 2279,
    "distance_lower_bound_scale": 0.824833527,
    "max_speed_kph": 70.0,
    "bounding_box": {
      "south": 10.7483071,
      "west": 106.6614172,
      "north": 10.806955,
      "east": 106.7194435
    }
  }
}
```

Metadata dataset còn ghi source timestamp, bbox query, license, attribution, stats và disclaimer. Client phải đọc response thay vì hard-code count/bounds vì dataset thay thế có thể khác.

## 6. `GET /graph`

```http
GET /api/v1/graph?scenario=normal&include_geojson=false&compact=true
```

| Query | Default | Meaning |
|---|---|---|
| `scenario` | `normal` | một enum scenario |
| `include_geojson` | `false` | populate FeatureCollection trùng geometry cho GIS client |
| `compact` | `false` | chỉ giữ attribute cần cho interactive map; không đổi node/edge/geometry |

Top-level response:

```text
dataset
summary
scenario
nodes[]
directed_edges[]
graph_geojson
```

### 6.1 Payload shaping cho React và GIS

React gọi `compact=true&include_geojson=false`. Mỗi `directed_edges[i].geometry` vẫn có polyline đầy đủ; `compact` chỉ bỏ provenance/tag chi tiết không dùng khi render. Bản coordinate trùng trong `directed_edges[i].attributes.geometry` luôn bị loại. `graph_geojson` vẫn có shape ổn định nhưng rỗng:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

Dùng `include_geojson=true` khi một GIS client thật sự cần FeatureCollection; khi đó `features` có 2.279 LineString. Không bật chỉ để render frontend vì sẽ buộc browser parse hai bản geometry tương đương.

### 6.2 Overlay nhẹ khi đổi scenario

Frontend tải topology/geometry một lần rồi chỉ gọi endpoint nhẹ này khi đổi scenario:

```http
GET /api/v1/traffic?scenario=heavy_rain
```

```json
{
  "scenario": {
    "id": "heavy_rain",
    "label": "Heavy rain",
    "description": "Reduced speeds, especially on bridges and higher-risk segments.",
    "base_multiplier": 1.34,
    "jitter": 0.22
  },
  "edges": [{
    "edge_id": "hcmc_edge_0000",
    "multiplier": 1.978806,
    "effective_speed_kph": 15.160657,
    "travel_time_s": 4.986591,
    "congestion": "severe",
    "closed": false
  }]
}
```

Response có đúng một status ngắn cho mỗi cung, không lặp node, topology hay geometry. React áp overlay theo `edge_id` và cập nhật style theo từng animation-frame chunk để tránh khóa main thread.

### 6.3 Node

```json
{
  "id": "poi_way_39514795",
  "name": "Chợ Bến Thành",
  "kind": "delivery_market",
  "lat": 10.7725474,
  "lon": 106.6979498,
  "attributes": {
    "osm_type": "way",
    "osm_id": 39514795,
    "delivery_destination": true,
    "delivery_category": "market",
    "routing_component": "primary"
  }
}
```

POI gồm market, supermarket, university, bus station và hospital. `delivery_hospital` chỉ là một category điểm giao/nhận và không được ưu tiên hay ép làm đích.

### 6.4 Directed edge

```json
{
  "id": "hcmc_edge_0000",
  "source": "osm_366476402",
  "target": "osm_366367996",
  "distance_m": 21.0,
  "speed_kph": 30.0,
  "road_name": "Trường Sa",
  "road_class": "tertiary",
  "risk": 0.3,
  "traversable": true,
  "direction": "one-way",
  "attributes": {
    "incident_prone": true,
    "base_congestion": 2.96
  },
  "geometry": [[106.6668087, 10.7905407], [106.6666537, 10.7906471]],
  "traffic": {
    "edge_id": "hcmc_edge_0000",
    "scenario": "normal",
    "multiplier": 1.213717,
    "effective_speed_kph": 24.717459,
    "free_flow_time_s": 2.52,
    "travel_time_s": 3.058567,
    "delay_s": 0.538567,
    "congestion": "moderate",
    "closed": false,
    "reason": "Normal traffic; snapshot baseline 2.96/5; stable edge variation"
  }
}
```

Mọi record runtime đã là một cung `source → target`. `direction="two-way"` cho biết cung bắt nguồn từ đoạn đường hai chiều; chiều ngược là một record khác. Không nhân đôi lại các record này.

`traversable` là gate của **mô hình** cùng với `traffic.closed`. Nó không phải xác nhận quyền lưu thông thực tế cho xe máy/ô tô/xe tải/người đi bộ. Snapshot không bao phủ đầy đủ turn restriction, biển cấm, lane restriction hoặc giờ cấm.

## 7. `POST /search`

### 7.1 Request

```json
{
  "start_id": "poi_way_152994798",
  "goal_id": "poi_way_39514795",
  "algorithm": "astar",
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "include_trace": true,
  "max_trace_events": 1000,
  "max_expansions": 100000,
  "include_alternative": true
}
```

PowerShell example:

```powershell
$body = @{
  start_id = 'poi_way_152994798'
  goal_id = 'poi_way_39514795'
  algorithm = 'astar'
  heuristic = 'travel_time'
  scenario = 'morning_rush'
  cost_weights = @{ distance=.25; travel_time=.5; traffic_delay=.2; risk=.05 }
  include_trace = $true
  max_trace_events = 1000
  max_expansions = 100000
  include_alternative = $true
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/search `
  -ContentType application/json -Body $body
```

### 7.2 Response

```text
request_id, status, found, start_id, goal_id,
algorithm, heuristic, scenario,
path, edge_ids, route_geojson,
metrics, trace, explanation, alternative, cost_breakdown
```

Important invariants khi `found=true`:

- `path[0] == start_id` và `path[-1] == goal_id`;
- `len(edge_ids) == len(path)-1`;
- `edge_ids[i]` nối đúng `path[i] → path[i+1]`;
- route geometry dùng `[longitude, latitude]`;
- `metrics.path_cost == cost_breakdown.total_cost == Σ cost_breakdown.components`.

`route_geojson` của backend là một GeoJSON geometry. Ví dụ rút gọn dưới đây chỉ minh họa shape và hai endpoint; response thật giữ toàn bộ intermediate coordinates:

```json
{
  "type": "LineString",
  "coordinates": [[106.6861395, 10.7672833], [106.6979498, 10.7725474]]
}
```

### 7.3 Trace

Trace envelope:

```json
{
  "schema_version": "1.0",
  "event_count": 42,
  "truncated": false,
  "events": []
}
```

Mỗi event luôn có:

```text
step, event, node_id, parent_id, edge_id, direction,
frontier_size, explored_count, g_cost, h_cost, f_cost,
depth, message
```

Event family: `start`, `iteration`, `expand`, `discover`, `relax`, `prune`, `finish`. Bidirectional Dijkstra dùng `direction=forward|backward`; thuật toán khác dùng `forward`. `max_trace_events` chỉ giới hạn dữ liệu lưu/transfer, còn search vẫn tiếp tục đến goal hoặc expansion limit.

### 7.4 Explanation and alternative

`explanation` gồm `summary`, `optimality`, `heuristic_note`, `traffic_note`, `cost_model`, `warnings`. Claim tối ưu phải đọc cùng algorithm, heuristic, scenario, weights và expansion limit.

`alternative` nếu có là candidate tốt nhất tìm được khi lần lượt loại một edge của primary route rồi chạy Dijkstra. Nó **không** phải chứng minh “second-shortest path” trên toàn không gian route.

## 8. `POST /compare`

Request nhận 2–8 algorithm duy nhất:

```json
{
  "start_id": "poi_way_152994798",
  "goal_id": "poi_way_39514795",
  "algorithms": ["bfs", "ucs", "astar", "greedy_best_first"],
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "include_trace": false,
  "max_trace_events": 300,
  "max_expansions": 100000
}
```

Response:

```text
request_id, start_id, goal_id, scenario,
runs[], ranking[], best_algorithm, agreement
```

`ranking` sắp found trước, sau đó weighted path cost, expanded nodes và ID. `best_algorithm` vì vậy nghĩa là best theo ranking này, không phải thuật toán nhanh nhất một cách tổng quát. `agreement` nhóm các run theo ordered `edge_ids`.

## 9. `POST /multi-route`

### 9.1 Request

```json
{
  "start_id": "poi_way_152994798",
  "stop_ids": [
    "poi_way_39514795",
    "poi_way_39598471",
    "poi_way_750511344",
    "poi_way_152993734"
  ],
  "method": "held_karp",
  "return_to_start": true,
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "seed": 42,
  "max_iterations": 1000,
  "max_expansions": 100000
}
```

Request hỗ trợ 1–12 stop; `held_karp` giới hạn 10. Stop phải duy nhất và khác start.

### 9.2 Response

```text
request_id, status, method, scenario,
start_id, requested_stop_ids, stop_order,
return_to_start, visit_sequence,
path, edge_ids, route_geojson,
segments[], metrics, cost_breakdown, explanation
```

Mỗi segment có `from_id`, `to_id`, `path`, `edge_ids`, `route_geojson`, `cost_breakdown`. Mọi pairwise leg dùng exact Dijkstra trên directed graph hiện tại.

Held–Karp “exact” chỉ có nghĩa thứ tự có tổng nhỏ nhất trên ma trận pairwise đã tính cho snapshot/scenario/weights và stop set đó. Nearest Neighbor, 2-opt và Simulated Annealing là approximate; seed làm SA tái lập được nhưng không làm nó thành exact.

## 10. Dataset connectivity relevant to clients

Snapshot bundled có:

- 1.103 node, 2.279 cung có hướng;
- 187 delivery POI;
- 85 strongly connected component;
- largest/primary SCC có 992 node và chứa 172 delivery POI.

Do graph có hướng và không phải mọi POI thuộc cùng SCC, khoảng cách địa lý gần không bảo đảm route hai chiều. UI/API phải xử lý `unreachable` hoặc `multi_route_unreachable`, không tự nối thẳng hai node để che lỗi topology.

## 11. Contract checks

- Unknown field bị 422; API không im lặng bỏ field.
- React client dùng `compact=true`; bản compact không duplicate geometry trong attributes/GeoJSON. Endpoint giữ `compact=false` làm mặc định để tương thích API.
- `include_geojson=true` trả đúng 2.279 feature cho snapshot bundled.
- Closed hoặc `traversable=false` edge không được dùng trong path.
- Start bằng goal trả path một node, zero edge và cost 0.
- Safe A* heuristic cho cùng optimum với UCS/Dijkstra khi không chạm limit.
- `traffic_aware` gỡ bỏ optimality guarantee của A*/IDA*.
- `limit_reached` không được trình bày là `unreachable`.
- Multi-route segments ghép đúng visit sequence và tổng component bằng total cost.

## 12. Safety boundary

API chứng minh hành vi thuật toán trên một graph giáo dục. OSM snapshot có thể cũ/thiếu; synthetic overlays không phải traffic live; `traversable` không mã hóa đầy đủ luật giao thông hay quyền đi của shipper. Không dùng output như turn-by-turn navigation, quyết định giao vận production, hoặc bằng chứng rằng một tuyến hợp pháp/an toàn cho xe máy.
