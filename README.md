# Đà Nẵng Route Intelligence Lab

Một web app full-stack để học, chạy và **nhìn thấy** các thuật toán tìm kiếm trên mạng đường có nguồn gốc OpenStreetMap ở trung tâm Đà Nẵng. Scenario là điều phối xe cấp cứu tới cơ sở y tế trong điều kiện giao thông đô thị Việt Nam; ứng dụng phục vụ bài lab AI, **không phải** hệ thống dispatch/navigation ngoài đời thật.

![A* route, trace playback and explanation](docs/assets/route-result.png)

## Điểm nổi bật

- FastAPI backend tự cài đặt thủ công 8 thuật toán: BFS, DFS, UCS, Dijkstra, A*, Greedy Best-First, Bidirectional Dijkstra và IDA*.
- 4 chiến lược multi-stop: Nearest Neighbor, Held–Karp exact, 2-opt và seeded Simulated Annealing.
- Graph OSM offline-first: **512 nodes, 1,007 directed edges**, 24 hospital POI; giữ one-way, tên/loại đường và polyline geometry.
- 5 scenario deterministic: normal, morning rush, evening rush, heavy rain và incident/closure.
- Cost minh bạch gồm distance, travel time, traffic delay và risk exposure; tùy chỉnh weights trực tiếp.
- Registry heuristic ghi rõ admissible/consistent: zero, Haversine, optimistic travel time; thêm traffic-aware để minh họa heuristic thực dụng nhưng không bảo đảm.
- React command center với OSM basemap, traffic layer, click-to-snap, visited/frontier/current-node animation, timeline playback, metrics, cost breakdown, alternative route và algorithm arena.
- Lời giải thích deterministic: nêu criterion, traffic impact, heuristic/optimality và so với route đối chứng.
- Backend test coverage hiện tại khoảng 89%; frontend có contract-adapter tests; dữ liệu và geometry có regression tests.

## Chạy nhanh trên Windows

Yêu cầu: Python 3.11–3.13, Node.js 20+ và npm.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

Sau đó mở:

- UI: <http://localhost:5173>
- FastAPI Swagger: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>

Hoặc chạy hai terminal riêng:

```powershell
# Terminal 1
cd backend
py -3.13 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm run dev
```

Kiểm tra toàn bộ:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

## Luồng sử dụng

1. Chọn `Tìm tuyến`, điểm đi/đến, scenario, algorithm, heuristic và objective.
2. Bấm **Tìm tuyến & tạo lời giải thích**.
3. Dùng timeline để phát, dừng, step hoặc đổi tốc độ; map tô current/frontier/visited/final route.
4. Mở `So sánh` để chạy 2–8 thuật toán trên **cùng** graph/scenario/weights.
5. Mở `Nhiều điểm`, chọn tối đa 12 stops; Held–Karp exact giới hạn 10 stops.
6. Mở `Thuật toán` để xem guarantee, complexity và độ an toàn của heuristic.

## Kiến trúc

```text
React + TypeScript + Leaflet + Recharts + Motion
                   │ REST /api/v1
                   ▼
FastAPI → cost/traffic/heuristic registries → 8 search runners
                   │
                   ├─ explanation + alternative-route engine
                   ├─ multi-stop optimizer
                   └─ bundled directed OSM snapshot (JSON)
```

Backend không dùng NetworkX cho search. Mọi algorithm trả cùng một normalized contract để UI dùng một renderer cho trace và metrics. API contract đầy đủ nằm trong [`docs/API.md`](docs/API.md), còn code backend nằm trong [`backend/app`](backend/app).

## Data và tính đúng đắn

Topology/tags/geometry được tải **một lần** bằng bounded Overpass query tại [`scripts/overpass_danang.ql`](scripts/overpass_danang.ql), sau đó contract bằng [`scripts/build_osm_snapshot.py`](scripts/build_osm_snapshot.py). Runtime routing chỉ đọc snapshot local; nó không gọi Overpass hay Nominatim.

- OSM cung cấp topology, coordinates, names, highway class, one-way và hospital POI.
- Congestion, incident, closure, flood susceptibility, risk và ETA là lớp **deterministic synthetic educational** có ghi provenance.
- Một hospital access connector được snap vào main strongly-connected component; tất cả 552 ordered hospital pairs đều reachable.
- Public Nominatim không được nhúng làm autocomplete mặc định. Chọn địa điểm dùng local graph index/map click để tránh vi phạm policy và để demo không phụ thuộc mạng.
- OSM tile chỉ tải cho viewport hiện tại, có attribution hiển thị; đặt `VITE_ENABLE_OSM_TILES=false` để chạy không basemap.

Chi tiết nguồn, schema, assumptions và cách refresh an toàn: [`docs/DATASET.md`](docs/DATASET.md). Dataset tuân theo ODbL 1.0; xem [`NOTICE.md`](NOTICE.md).

## Cấu trúc project

```text
backend/                 FastAPI, algorithms, optimizers, tests, datasets
frontend/                React/Vite UI và API adapter tests
scripts/                 setup/dev/check + bounded OSM snapshot pipeline
docs/                    report, rubric matrix, API, demo-video script
README.md                hướng dẫn tổng quan
```

## Tài liệu nộp lab

- [`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md): report đầy đủ, có placeholder thông tin nhóm/screenshots.
- [`docs/ALGORITHM_REFERENCE.md`](docs/ALGORITHM_REFERENCE.md): nguyên lý, complexity, completeness, optimality và heuristic.
- [`docs/RUBRIC_CHECKLIST.md`](docs/RUBRIC_CHECKLIST.md): map từng mục rubric sang code/demo evidence.
- [`docs/DEMO_VIDEO_SCRIPT.md`](docs/DEMO_VIDEO_SCRIPT.md): kịch bản video đúng yêu cầu đề.
- [`docs/DATASET.md`](docs/DATASET.md): provenance và data dictionary.

Trước khi nộp, nhóm vẫn cần điền thông tin thành viên, thêm ảnh chụp thật, export report/slides PDF/PPTX, quay video và đóng gói theo đúng `[GroupID].zip` của đề.

## Safety

Đây là mô phỏng học thuật. Không dùng output làm chỉ dẫn điều phối xe cấp cứu, điều hướng hoặc quyết định an toàn. Basemap và snapshot có thể cũ/thiếu; traffic không phải dữ liệu live.
