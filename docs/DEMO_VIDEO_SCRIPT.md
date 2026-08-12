# Demo Video Script — HCMC Delivery Route Lab

> Chưa quay. Đây là runbook/narration cho final commit; thay presenter, commit và test output trước khi ghi hình.

## 1. Production card

| Item | Value |
|---|---|
| Target length | 12–14 phút |
| Capture | 1080p, browser zoom 90–100% |
| UI | `http://localhost:5173` |
| API proof | `http://127.0.0.1:8000/docs` |
| Dataset | `hcmc-city-centre-delivery-osm-2026`, v2.0.0 |
| Primary pair | Co.op Mart → Chợ Bến Thành |
| Scenario | `morning_rush` |
| Weights | `.25 / .50 / .20 / .05` |
| Presenter | `[[Name]]` |
| Final commit | `[[SHA]]` |

Footer phải đọc được khi map xuất hiện:

> © OpenStreetMap contributors · ODbL 1.0 · ETA/congestion/risk are deterministic educational estimates—not live or motorbike-legal navigation.

## 2. Original mini delivery graph

Dùng một hình do nhóm tự vẽ, không lấy từ tutorial. Bối cảnh: shipper rời hub `H` để giao tại `D`.

```text
            cost 1            cost 8
      H ─────────────► A ─────────────► D
      │                                  ▲
      │ cost 2                           │ cost 2
      ▼                                  │
      B ─────────────► C ────────────────┘
            cost 2            cost 2
```

| Route | Hops | Composite cost |
|---|---:|---:|
| `H → A → D` | 2 | 9 |
| `H → B → C → D` | 3 | 6 |

Suggested admissible illustration: `h(H)=5`, `h(A)=7`, `h(B)=4`, `h(C)=2`, `h(D)=0`.

Điểm cần nói:

- BFS chọn route 2 hop nhưng cost 9;
- UCS/Dijkstra chọn route cost 6;
- A* với admissible `h` cũng tìm cost 6;
- DFS phụ thuộc thứ tự adjacency;
- Greedy chỉ nhìn `h`, nên không có weighted-optimal guarantee;
- đây là graph minh họa, không phải số liệu từ HCMC snapshot.

## 3. Timeline and narration

### 00:00–00:35 — Cold open

**On screen:** HCMC dashboard, route result đã chạy, playback dừng giữa trace.

**Narration:**

> “Một tuyến ít chặng chưa chắc có tổng chi phí giao hàng tốt nhất. Project mô hình hóa mạng đường trung tâm Thành phố Hồ Chí Minh thành graph có hướng, rồi cho chúng ta nhìn trực tiếp cách BFS, DFS, UCS, A* và bốn thuật toán bổ sung mở rộng graph. Cost kết hợp distance, ETA mô phỏng, traffic delay và risk exposure.”

### 00:35–01:20 — Problem and safety boundary

**On screen:** title/overview và disclaimer.

**Narration:**

> “Bài toán là hỗ trợ học thuật cho shipper/courier: chọn điểm lấy hàng hoặc điểm đi, điểm giao, và có thể tối ưu nhiều điểm. Đây không phải navigation production. OSM là snapshot; traffic, road disruption, flood susceptibility và risk là ước lượng deterministic. Field traversable chỉ có nghĩa cung được dùng trong mô hình, không chứng nhận đường hợp pháp cho xe máy hay bất kỳ phương tiện cụ thể nào.”

### 01:20–02:10 — Dataset

**On screen:** dataset facts, small provenance diagram.

```text
raw Overpass + processed teammate export
                  │ validation / unit mapping / direction audit
                  ▼
backend/data/hcmc_delivery_osm_snapshot.json
                  │ runtime load only
                  ▼
FastAPI + React
```

**Narration:**

> “Runtime không đọc data-tmp. Importer fail-fast chuẩn hóa source thành canonical JSON và ghi source checksum. Snapshot có 1.103 node, 2.279 cung có hướng và 187 delivery POI. Có 85 strongly connected component; primary component có 992 node và chứa 172 POI. Vì graph có hướng, hai điểm gần nhau vẫn có thể không reachable hai chiều.”

**On-screen facts:**

- 916 contracted road nodes + 187 delivery POIs = 1.103 nodes;
- 1.039 one-way arcs + 1.240 two-way-derived arcs = 2.279 directed arcs;
- 172/187 delivery POIs in primary SCC;
- OSM base timestamp `2026-08-05T16:31:02Z`.

### 02:10–03:05 — Graph and cost model

**On screen:** one canonical node/edge and cost formula.

**Narration:**

> “State là node hiện tại; action là đi qua outgoing edge còn traversable và không bị scenario đóng; goal test là node hiện tại bằng delivery destination. Mỗi runtime record đã là một cung source-to-target. Source two-way đã có reverse record riêng, nên loader tuyệt đối không nhân đôi lần nữa.”

```text
C(e) = ŵd·distance_km
     + ŵt·travel_minutes
     + ŵc·delay_minutes
     + ŵr·(risk × distance_km)
```

> “UI objective chỉ là weight preset. Backend nhận bốn weight và normalize tỷ lệ; không có vehicle parameter giả.”

### 03:05–05:05 — Algorithms on the mini graph

#### BFS and DFS

> “BFS dùng FIFO và mở rộng theo depth. Nó chọn H-A-D vì chỉ có 2 hop, nhưng composite cost là 9. DFS dùng LIFO, đi sâu theo adjacency order và không tối ưu hop hoặc weighted cost.”

#### UCS and Dijkstra

> “UCS luôn pop frontier có g nhỏ nhất. Trên model này Dijkstra và UCS dùng cùng core, nên cùng chọn H-B-C-D với cost 6. Guarantee dựa trên edge cost không âm.”

#### A*

**On screen:** `f=g+h` values.

> “A* chọn minimum g+h. Với calibrated Haversine hoặc optimistic travel-time, h là admissible và consistent cho cost implementation, nên goal đầu tiên được pop là optimum nếu không chạm expansion limit.”

#### Greedy, Bidirectional, IDA*

> “Greedy chỉ nhìn h nên có thể mở rộng ít nhưng route tệ. Bidirectional Dijkstra chạy forward bằng outgoing edges và backward bằng incoming edges—đây là điều bắt buộc trên directed graph. IDA* tiết kiệm active frontier memory nhưng re-expand rất nhiều và có thể chạm max-expansions.”

**Summary card:**

```text
BFS: minimum hops only
DFS: adjacency-sensitive
UCS/Dijkstra: weighted optimum, non-negative costs
A*: weighted optimum with safe h
Greedy: no optimum guarantee
Bidirectional Dijkstra: exact, directed two-wave
IDA*: conditional; operational limit matters
```

### 05:05–05:45 — Heuristics

**On screen:** metadata registry.

> “Zero, calibrated Haversine và optimistic travel-time là safe. Snapshot hiện có scale khoảng 0,824833527 và maximum speed 70 km/h; backend tính lại khi load dataset khác. Traffic-aware project local mean multiplier đến goal nên có thể overestimate; dùng nó sẽ gỡ guarantee của A* và IDA*.”

### 05:45–06:25 — Architecture and compact graph API

**On screen:** architecture diagram, Swagger `/graph` parameters.

> “FastAPI cung cấp health, metadata, graph, traffic overlay, search, compare và multi-route. React tải graph compact một lần: geometry nằm một lần ở directed-edges và GeoJSON FeatureCollection rỗng. Khi đổi scenario, UI chỉ lấy status cạnh từ traffic endpoint rồi restyle theo từng frame nhỏ. Việc này giảm parse, allocation và long task trên main thread.”

### 06:25–08:10 — Live Route mode

Set input:

```text
Start: poi_way_152994798 — Co.op Mart
Goal:  poi_way_39514795  — Chợ Bến Thành
Algorithm: A*
Heuristic: travel_time
Scenario: morning_rush
Weights: .25 / .50 / .20 / .05
```

**Actions:**

1. chỉ start/goal marker và directed network;
2. bấm tìm tuyến;
3. pause playback ở giữa;
4. step hai hoặc ba frame;
5. chỉ current edge, explored tree và frontier links;
6. đi tới final route, metrics, cost breakdown, explanation;
7. mở alternative card.

**Narration:**

> “Frame không phải một dot nhảy ngẫu nhiên. Frontend reconstruct parent links từ trace để vẽ cây đã khám phá, frontier candidate và active edge. Với case này A* tìm weighted cost 4,781696, quãng đường 2 483 m, ETA mô phỏng 434,741 giây và mở rộng 470 node.”

> “A* được gọi là optimum ở đây vì travel-time heuristic safe và run không chạm limit. Claim chỉ đúng cho snapshot, scenario, weights và implemented cost—không phải bảo đảm route ngoài đời.”

> “Alternative là candidate tốt nhất từ việc loại từng primary edge rồi chạy Dijkstra; không gọi nó là second-shortest path đầy đủ.”

### 08:10–09:00 — Scenario sensitivity

**On screen:** table/chart từ actual rerun.

| Scenario | Cost | Distance (m) | ETA (s) |
|---|---:|---:|---:|
| normal | 3.486893 | 2 588 | 318.508 |
| morning rush | 4.781696 | 2 483 | 434.741 |
| evening rush | 5.272845 | 2 792 | 466.168 |
| heavy rain | 5.289770 | 2 616 | 473.116 |
| road disruption | 4.287072 | 2 588 | 387.095 |

> “Cùng start/goal và weight, scenario đổi ETA và có thể đổi topology optimum. Road-disruption hiện đóng 47 directed arc deterministic. Không có feed live và không random tại request time.”

### 09:00–10:15 — Compare mode

**On screen:** BFS, UCS, A*, Greedy; optionally show all eight table.

Key actual results:

| Algorithm | Status | Cost | Expanded | Hops |
|---|---|---:|---:|---:|
| BFS | found | 5.093109 | 444 | 17 |
| UCS | found | 4.781696 | 723 | 22 |
| A* | found | 4.781696 | 470 | 22 |
| Greedy | found | 6.099368 | 50 | 29 |
| Bidirectional Dijkstra | found | 4.781696 | 265 | 22 |
| IDA* | limit reached | — | 100.000 | — |

> “BFS có ít hop hơn nhưng cost cao hơn. Greedy mở rộng ít nhưng không optimum. A* giảm expansion so với Dijkstra, còn Bidirectional Dijkstra giảm mạnh ở case này. IDA* chạm 100 nghìn expansion; phải nói limit-reached, không nói unreachable. Runtime muốn so sánh nghiêm túc phải warm-up và dùng median/IQR.”

### 10:15–11:35 — Multi-stop

Input:

```text
Start: Co.op Mart
Stops: Chợ Bến Thành, Chợ Tân Định,
       Co.opmart Rạch Miễu,
       Trường Đại học Sài Gòn – cơ sở chính
Return to start: yes
Scenario: morning_rush
```

| Method | Cost | Distance (m) | ETA (min) |
|---|---:|---:|---:|
| Nearest Neighbor | 27.202982 | 16 057 | 39.783 |
| NN + 2-opt | 25.924372 | 15 187 | 37.975 |
| Held–Karp | 25.924372 | 15 187 | 37.975 |
| Seeded SA + 2-opt | 25.924372 | 15 187 | 37.975 |

> “Mỗi pairwise leg dùng exact Dijkstra. Held–Karp tìm order exact trên directed pairwise matrix và giới hạn 10 stop. 2-opt giảm 4,7003 phần trăm so với Nearest Neighbor trong case này và tình cờ trùng exact result; điều đó không chứng minh 2-opt hay SA luôn optimum.”

**Show:** requested order, optimized order, visit sequence và từng segment; không chỉ vẽ một polyline tổng.

### 11:35–12:20 — Validation and failure states

**On screen:** một structured 422 và Learn tab.

> “Strict request model reject unknown field. Unknown node, duplicate stop và quá nhiều Held–Karp stop có error envelope rõ. Unreachable do directed components khác expansion-limit. UI phải render trạng thái lỗi thân thiện, không leak traceback, JSON debug hoặc internal identifier không cần thiết.”

### 12:20–13:15 — Limitations and ethics

> “Snapshot bounded bỏ nhiều hẻm/residential road; turn restriction, lane, giờ cấm và công trường có thể thiếu. 15 delivery POI nằm ngoài primary SCC. POI connector là dữ liệu derived, không bảo đảm đúng cổng. Traffic, ETA và risk không live. Traversable không xác nhận tuyến hợp pháp cho xe máy. Multi-stop chưa có capacity, time window, service time hay nhiều shipper.”

### 13:15–13:40 — Closing

> “Project đáp ứng directed graph, cost bốn thành phần, bốn thuật toán bắt buộc, bốn thuật toán bổ sung, multi-stop, trace playback, metrics và explanation. Giá trị chính là nhìn thấy tại sao các search strategy khác nhau—không phải giả vờ thay thế navigation production.”

## 4. Shot list

| Shot | Required evidence |
|---|---|
| 1 | HCMC branding + OSM attribution + dataset online |
| 2 | Original mini delivery graph |
| 3 | Dataset provenance/counts/SCC |
| 4 | Cost formula + edge direction |
| 5 | Algorithm/heuristic registry |
| 6 | Swagger compact `include_geojson` behavior |
| 7 | A* setup and result |
| 8 | Playback current/frontier/explored tree |
| 9 | Cost breakdown/explanation/alternative |
| 10 | Scenario sensitivity |
| 11 | Compare result |
| 12 | Multi requested/optimized order + segments |
| 13 | Structured validation error |
| 14 | Limitations + final test summary |

## 5. Recording runbook

### Before recording

- [ ] Freeze commit and canonical dataset.
- [ ] Run `scripts/check.ps1` successfully.
- [ ] Verify `/health` reports 1.103/2.279 and v2.0.0.
- [ ] Verify no console error in all four modes.
- [ ] Clear stale query/cache and reload once.
- [ ] Preselect exact IDs above.
- [ ] Confirm HCMC viewport and attribution readable.
- [ ] Remove debug panels, inspector overlays and notification noise.
- [ ] Update every screenshot/table if code/data changed.

### During recording

- [ ] Không cắt trước khi request/result state hoàn tất.
- [ ] Di chuyển cursor chậm; highlight control trước khi click.
- [ ] Pause playback để giải thích frontier tree.
- [ ] Đọc đúng `limit_reached`, `unreachable`, `exact`, `approximate`.
- [ ] Không gọi synthetic overlay là live.
- [ ] Không gọi traversable là legal vehicle access.

### After recording

- [ ] Kiểm tra audio, Vietnamese diacritics và map labels ở 1080p.
- [ ] OSM attribution/disclaimer xuất hiện đủ lâu.
- [ ] Không lộ path local, token, terminal secret hoặc debug traceback.
- [ ] Link video mở được trong private window.
- [ ] Transcript/slide dùng cùng facts với final commit.

## 6. Q&A crib sheet

**Why not use a complete map/navigation engine?**

Lab tập trung search algorithms. Dataset là bounded directed snapshot và UI là visual laboratory; production navigation cần live data, legal vehicle profiles, turn restrictions và operational systems khác.

**Why can A* be optimal?**

Khi dùng calibrated Haversine hoặc optimistic travel-time, heuristic là admissible/consistent cho implemented non-negative cost, và run không chạm expansion cap.

**Why is traffic-aware unsafe for that claim?**

Local mean multiplier có thể overestimate true remaining cost và vi phạm consistency.

**Why can nearby POIs be unreachable?**

Graph có hướng và có 85 SCC; proximity không tạo directed path.

**Is Held–Karp globally optimal?**

Chỉ exact trên computed directed pairwise matrix cho stop set, scenario, weights và return flag hiện tại, tối đa 10 stop, khi pair searches hoàn tất.

**Does `traversable=true` mean a motorbike may legally use the road?**

Không. Đó chỉ là model gate. Snapshot không đủ dữ liệu để xác nhận legal access cho một vehicle profile.

**Why is compact graph API useful?**

Frontend vẫn nhận mỗi edge polyline một lần nhưng không phải parse bản duplicate trong attributes và GeoJSON; GIS clients có thể opt in bằng `include_geojson=true`.
