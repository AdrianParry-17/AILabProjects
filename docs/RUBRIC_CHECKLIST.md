# Lab 1 Rubric & Submission Checklist — HCMC Delivery Route Lab

Dùng file này làm release gate. “Có evidence” nghĩa code/tài liệu đã tồn tại; không đồng nghĩa final PDF, slide, ảnh hoặc video đã được tạo.

Status:

- ✅ implementation/document evidence có sẵn;
- 🧪 phải chạy/chụp lại trên final commit;
- 🧑 cần nhóm hoàn thiện thủ công;
- ⚠️ claim phải kèm điều kiện/giới hạn.

## 1. Evaluation matrix

| Criterion | Pts | Evidence hiện tại | Final gate | Status |
|---|---:|---|---|---|
| Bối cảnh giao thông Việt Nam | 10 | courier/delivery ở trung tâm TP.HCM; scenario congestion/rain/disruption | demo một thay đổi scenario làm đổi ETA hoặc route | ✅ 🧪 |
| Graph, dataset, cost | 15 | 1.103 node, 2.279 directed arc, 187 POI; cost bốn thành phần | verify checksum/provenance và giải thích topology vs overlay | ✅ 🧪 |
| BFS, DFS, UCS, A* | 20 | cùng normalized result/trace contract | chạy backend tests và demo frontier khác nhau | ✅ 🧪 |
| Ít nhất hai thuật toán bổ sung | 10 | Dijkstra, Greedy, Bidirectional Dijkstra, IDA* | trình bày guarantee/limit đúng | ✅ ⚠️ |
| Nhiều delivery location | 10 | NN, Held–Karp, 2-opt, seeded SA; pairwise Dijkstra | demo requested order, optimized order, segments | ✅ 🧪 |
| GUI và visual search | 10 | React/Leaflet trace tree, playback, metrics, Compare, Learn | desktop+narrow viewport, console sạch | ✅ 🧪 |
| Explanation/alternative | 10 | cost breakdown, optimality note, bounded alternative | kể tên một khác biệt route và giới hạn alternative | ✅ ⚠️ |
| Báo cáo kỹ thuật | 10 | report/API/dataset/algorithm docs | điền nhóm, ảnh final, test output, export PDF | ✅ 🧑 |
| Video | 5 | script/shot plan | quay, edit, kiểm tra link/audio/readability | 🧑 |

## 2. Requirement traceability

### 2.1 Submission package

- [ ] Nhóm có đúng số thành viên theo đề chính thức.
- [ ] Chỉ định một đại diện.
- [ ] ZIP dùng đúng tên mà giảng viên yêu cầu.
- [ ] Có source-code link, report PDF, slide, video link và data/data-description.
- [ ] Mọi link mở được trong cửa sổ private không đăng nhập owner.
- [ ] Extract ZIP trên một đường dẫn sạch và chạy thử trước khi nộp.
- [ ] Không đóng gói secret, `.env`, virtualenv, `node_modules`, cache hoặc `backend/data-tmp`.

### 2.2 Problem framing

- [x] Thành phố Hồ Chí Minh, không phải city cũ.
- [x] Bài toán shipper/courier: điểm lấy hàng/điểm đi → điểm giao.
- [x] Multi-stop là nhiều delivery location.
- [x] FastAPI + React là thay đổi stack có chủ đích so với Streamlit proposal.
- [x] UI/API/docs không dựa trên semantics y tế hoặc xe chuyên dụng.
- [x] Disclaimer nói rõ educational, không phải navigation live.
- [x] Không claim `traversable` đồng nghĩa hợp pháp cho xe máy.
- [ ] Final report có formal state, goal, transition và một graph minh họa do nhóm tự vẽ.

### 2.3 Graph and edge contract

- [x] Directed graph với outgoing/incoming indexes.
- [x] Node là intersection/gateway/bridge access hoặc delivery POI.
- [x] Edge có start/end, distance, time/speed, congestion, risk và direction.
- [x] Canonical records đã là directed arc; không double-expand source `two-way` rows.
- [x] Source `two-way` arc được importer xác nhận có reverse record.
- [x] `traversable` thay cho access field gắn domain cũ.
- [x] Closed hoặc non-traversable edge bị loại khỏi transitions.
- [x] Geometry có GeoJSON coordinate order và được orient theo source→target.
- [ ] Demo một one-way constraint hoặc unreachable case có giải thích.

### 2.4 Cost and scenario

- [x] Distance + travel time + traffic delay/congestion + risk exposure.
- [x] Weight không âm, tổng dương và được normalize.
- [x] UI có Shortest distance, Fastest ETA, Balanced preset.
- [x] Normal, morning/evening rush, heavy rain và road disruption.
- [x] Snapshot baseline congestion được đưa vào deterministic multiplier.
- [x] Request-time overlay không random.
- [ ] Presentation phân biệt source congestion score `1–5`, multiplier và weighted cost component.
- [ ] Show ít nhất một scenario/weight làm thay đổi route hoặc ETA.

### 2.5 Dataset and provenance

- [x] ≥20 node: **1.103**.
- [x] ≥30 directed edge: **2.279**.
- [x] **187** delivery POI.
- [x] **85** SCC; primary SCC **992** node.
- [x] **172/187** delivery POI thuộc primary SCC.
- [x] **1.039** source one-way arc và **1.240** two-way-derived arc.
- [x] OSM base timestamp, query bbox, source hashes và IDs được giữ.
- [x] Runtime đọc `backend/data/hcmc_delivery_osm_snapshot.json`.
- [x] `backend/data-tmp/` chỉ là ignored import workspace.
- [x] Reproducible fail-fast importer ở `scripts/import_hcmc_snapshot.py`.
- [x] OSM attribution/ODbL được giữ trên UI/docs.
- [x] Canonical SHA-256: `9D803A77A88418A5512F3098D859FD28CBA6539AE92E12D9394EE2E39C8D2A37`.
- [ ] Rerun importer và hash check trên final commit.

### 2.6 Pair-search algorithms

- [x] BFS.
- [x] DFS.
- [x] UCS.
- [x] A*.
- [x] Dijkstra.
- [x] Greedy Best-First.
- [x] Bidirectional Dijkstra dùng incoming graph ở backward wave.
- [x] IDA*.
- [x] Unified path/edge/metrics/trace output.
- [x] `limit_reached` tách khỏi `unreachable`.
- [ ] Final comparison dùng cùng start/goal/scenario/weights/expansion cap.
- [ ] Video chỉ ra BFS minimum hops không đồng nghĩa minimum weighted cost.

### 2.7 Heuristics

- [x] `zero` baseline.
- [x] calibrated Haversine lower bound.
- [x] optimistic travel-time lower bound.
- [x] experimental `traffic_aware` estimate.
- [x] Metadata công bố admissible/consistent.
- [x] Snapshot calibration `s≈0.824833527`, `v_max=70 km/h` được tính lúc load.
- [ ] Demo nói rõ `traffic_aware` gỡ optimality guarantee A*/IDA*.

### 2.8 Multi-location

- [x] Nearest Neighbor baseline.
- [x] NN + 2-opt local improvement.
- [x] Held–Karp exact trên directed pairwise matrix, ≤10 stops.
- [x] Seeded Simulated Annealing + 2-opt.
- [x] Request tổng quát giới hạn 12 stop.
- [x] Return-to-start option.
- [x] Response có requested order, optimized order, visit sequence và per-leg segments.
- [x] UI giữ và render per-leg segments, distance, ETA và cost trong Route Intelligence.
- [ ] Demo exact-vs-approximate và không suy rộng từ một case trùng optimum.

### 2.9 GUI and visualization

- [x] React web UI localhost.
- [x] HCMC graph/map, delivery category và OSM attribution.
- [x] Chọn start, goal, stop bằng list/map.
- [x] Algorithm, heuristic, objective weights và scenario controls.
- [x] Current node, frontier links, explored tree và final route.
- [x] Timeline play/pause/step/speed.
- [x] Distance, ETA, cost, expanded, frontier peak, runtime.
- [x] Cost breakdown, explanation, alternative.
- [x] Compare, Multi-stop, Learn.
- [x] Backend loading/error states.
- [x] Không còn user-facing debug text.
- [x] Không còn branding/icon/label của domain cũ.
- [x] Test interaction responsiveness trên full 1.103/2.279 graph.
- [x] Desktop và viewport khoảng 430 px không overflow.
- [ ] OSM tiles disabled vẫn thấy graph/route.

### 2.10 Compact graph API

- [x] `/graph` default `include_geojson=false`.
- [x] Default vẫn giữ `directed_edges[].geometry`.
- [x] Duplicate `attributes.geometry` không đi qua response.
- [x] Default `graph_geojson.features` rỗng, giữ stable shape.
- [x] `include_geojson=true` dành cho GIS client và trả 2.279 feature.
- [x] `compact=true` giữ nguyên topology/geometry và lọc attribute không dùng trên map.
- [x] `/traffic` đổi scenario mà không lặp nodes/geometry.
- [x] Regression test payload compact/full có cùng topology/edge geometry semantics.

## 3. Report and evidence gate

| Required section | Evidence | Final action |
|---|---|---|
| Group introduction | `TECHNICAL_REPORT.md` §A | điền tên/ID/contribution |
| Problem context | §2 | giữ courier/delivery framing |
| Problem model/cost | §3 | kiểm tra formula khi export |
| Dataset | §4 + `DATASET.md` | giữ checksum/provenance/limitations |
| Algorithms/heuristics | §5–6 + `ALGORITHM_REFERENCE.md` | không vượt claim guarantee |
| Multi-location | §7/§10.3 | ảnh requested vs optimized order |
| Architecture/flow | §8–9 | render diagram đúng |
| Experiment | §10 | rerun trên final commit |
| GUI instructions | §11 | ảnh HCMC thật, không dùng ảnh cũ |
| Limitations/future | §13–14 | giữ vehicle/legal/live caveats |

### Screenshot list

- [x] Route mode trước khi chạy; input/control rõ (`dashboard-overview.png`).
- [x] A* result với HCMC map, metrics, explanation (`route-result.png`).
- [x] Playback đang chạy với current/frontier/explored tree (`route-result.png`).
- [x] Alternative route/card (`route-result.png`).
- [x] Compare ít nhất 4 algorithm (`algorithm-compare.png`).
- [x] Multi-stop requested/optimized order và segments (`multi-stop.png`).
- [x] Heavy Rain hoặc Road Disruption (`heavy-rain.png`).
- [x] Learn view với admissibility (`algorithm-learn.png`).
- [x] Optional Swagger graph compact parameter.

Mỗi caption ghi input IDs/names, algorithm, heuristic, scenario, weights, commit và OSM attribution.

## 4. Automated verification

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

Ngoài suite, smoke test:

- [ ] `/health`: dataset v2.0.0, 1.103 node, 2.279 edge.
- [ ] `/metadata`: 8 algorithm, 4 heuristic, 5 scenario, 4 multi method.
- [x] `/graph` compact: 2.279 edge, zero GeoJSON features, không duplicate geometry.
- [x] `/graph?include_geojson=true`: 2.279 GeoJSON features.
- [ ] `incident`: 47 directed arc đóng trong snapshot hiện tại.
- [ ] A* safe heuristic trả same optimum với Dijkstra trên controlled case.
- [ ] IDA* limit case báo `limit_reached`, không báo unreachable.
- [ ] Compare reject duplicate algorithm.
- [ ] Held–Karp reject >10 stop.
- [ ] Multi exact case trong primary SCC thành công.
- [ ] Unknown node trả structured 422.
- [ ] Start=goal trả zero cost.
- [ ] Frontend backend-offline state không blank/crash.
- [ ] Browser console không có uncaught error ở bốn mode.

Record sau khi chạy final:

| Check | Final value |
|---|---|
| Commit | `[[SHA]]` |
| Python / OS | `[[value]]` |
| Node / npm | `[[value]]` |
| Backend tests / coverage | `[[value]]` |
| Frontend unit/build/E2E | `[[value]]` |
| Dataset hash | `[[value]]` |

## 5. Demo/video gate

- [ ] Có mini graph tự thiết kế cho delivery, không sao chép tutorial.
- [ ] Giải thích start, goal, frontier, expansion order.
- [ ] Nói đúng `g`, `h`, `f` cho từng family.
- [ ] Demo actual HCMC route.
- [ ] Demo BFS vs weighted optimum.
- [ ] Demo A* heuristic condition.
- [ ] Demo scenario sensitivity.
- [ ] Demo multi exact vs approximate.
- [ ] Nói rõ synthetic overlays và snapshot timestamp.
- [ ] Nói rõ không phải live/motorbike-legal navigation.
- [ ] OSM attribution đọc được.
- [ ] Audio/cursor/text rõ ở final resolution.
- [ ] Link video mở được không cần quyền edit.

## 6. Presentation slide gate

Suggested deck:

1. team/contribution;
2. HCMC courier delivery problem;
3. hybrid OSM/synthetic dataset;
4. directed graph + cost;
5. required algorithms;
6. extra algorithms + heuristic conditions;
7. architecture + compact graph API;
8. measured pair/scenario comparison;
9. multi-stop exact vs approximate;
10. limitations, attribution, conclusion.

- [ ] Không nói traffic là live.
- [ ] Không nói `traversable` là legal access cho xe máy.
- [ ] Không nói BFS/DFS/Greedy weighted-optimal.
- [ ] Không nói A* optimal mà thiếu heuristic/limit condition.
- [ ] Không nói IDA* `limit_reached` là unreachable.
- [ ] Không nói Held–Karp giải global real-world delivery plan.
- [ ] Runtime chart ghi environment và repetition protocol.

## 7. “Make no mistake” claim audit

| Risky claim | Correct wording |
|---|---|
| “real-time/live traffic” | deterministic educational scenario overlay |
| “real road data” | OSM snapshot topology/tags; derived/synthetic time/congestion/risk |
| “optimal route” | optimum theo objective, snapshot, scenario, weights, algorithm condition và expansion budget |
| “shortest” | nói rõ minimum hops, distance hay weighted cost |
| “A* is fastest” | chỉ nêu measured result với environment/repetitions |
| “IDA* unreachable” | phân biệt `limit_reached` và `unreachable` |
| “second-shortest route” | bounded single-primary-edge-exclusion alternative |
| “Held–Karp solves delivery globally” | exact trên computed directed pairwise matrix, ≤10 stops |
| “two-way edge” | hai directed records đã tồn tại; không double-expand |
| “traversable for shipper/motorbike” | traversable trong model; không xác nhận legal vehicle access |
| “delivery hospital is a medical destination” | category POI giao/nhận; không đánh giá dịch vụ y tế |

Trước khi nộp, dùng `rg -n -i` để audit toàn repository cho mọi tên thành phố, domain, vehicle và access field legacy; loại `backend/data-tmp`, dependency và build output khỏi phạm vi. Mọi match còn lại phải là migration/history được giải thích rõ hoặc phải sửa.

## 8. Packaging rehearsal

- [ ] Freeze code và canonical dataset.
- [ ] Rerun importer, tests, benchmarks và screenshots sau freeze.
- [ ] Kiểm tra Vietnamese font, formulas, tables, diagrams và links trong PDF.
- [ ] Xóa mọi `[[...]]` placeholder khỏi artifact nộp.
- [ ] Không đưa `backend/data-tmp`, cache, build output hoặc secret vào ZIP.
- [ ] Giữ canonical data hoặc data link/description đúng yêu cầu.
- [ ] Verify source/video link permissions và expiration.
- [ ] So sánh ZIP cuối với từng filename trong đề chính thức.
