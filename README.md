# HCMC Delivery Route Intelligence Lab

Một ứng dụng full-stack chạy trên localhost để học, chạy và trực quan hóa các thuật toán tìm kiếm trên mạng đường trung tâm Thành phố Hồ Chí Minh. Bối cảnh là lập tuyến cho courier/shipper: một điểm lấy hàng, một điểm giao hàng, hoặc nhiều điểm cần ghé. Đây là phòng thí nghiệm AI dùng snapshot OpenStreetMap và lớp giao thông mô phỏng, không phải hệ thống điều hướng thời gian thực.

> Phạm vi dữ liệu là một ô trung tâm thành phố, không phải toàn bộ địa giới Thành phố Hồ Chí Minh. Kết quả chỉ dùng cho học tập và demo.

## Điểm nổi bật

- FastAPI backend tự cài đặt 8 thuật toán: BFS, DFS, UCS, Dijkstra, A*, Greedy Best-First, Bidirectional Dijkstra và IDA*.
- 4 chiến lược cho hành trình nhiều điểm: Nearest Neighbor, Held–Karp exact, 2-opt và seeded Simulated Annealing.
- Snapshot canonical offline-first có **1.103 node và 2.279 cung có hướng**. Mỗi record đã là một cung; loader không nhân đôi các record được nguồn gắn nhãn two-way.
- 187 POI giao nhận từ năm nhóm OSM: chợ, siêu thị, trường đại học, bệnh viện và bến xe buýt.
- 172 POI nằm trong strongly connected component chính gồm 992 node. Dataset có tổng cộng 85 SCC và metadata đánh dấu rõ node primary/peripheral để client chọn điểm an toàn hơn.
- 5 kịch bản deterministic: normal, morning rush, evening rush, heavy rain và road disruption.
- Hàm chi phí minh bạch gồm distance, travel time, traffic delay và risk exposure; người dùng có thể thay đổi weights.
- Registry heuristic ghi rõ admissible/consistent: zero, Haversine, optimistic travel time và traffic-aware.
- React/Vite UI có OSM basemap, chọn điểm trên bản đồ, phát lại cây tìm kiếm, metrics, cost breakdown, tuyến đối chứng và benchmark thuật toán.

## Chạy nhanh trên Windows

Yêu cầu: Python 3.11–3.13, Node.js 20+ và npm.

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
~~~

Sau đó mở:

- UI: <http://localhost:5173>
- FastAPI Swagger: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>

Hoặc chạy hai terminal riêng:

~~~powershell
# Terminal 1
cd backend
py -3.13 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm run dev
~~~

Kiểm tra toàn bộ project:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
~~~

## Luồng sử dụng

1. Mở <strong>Tìm tuyến</strong>, chọn điểm lấy hàng và điểm giao hàng.
2. Chọn traffic scenario, thuật toán, heuristic và objective.
3. Bấm <strong>Tìm tuyến & tạo lời giải thích</strong>.
4. Dùng timeline để phát, dừng hoặc step qua current node, frontier và cây đã khám phá.
5. Mở <strong>So sánh</strong> để chạy 2–8 thuật toán trên cùng graph, scenario và weights.
6. Mở <strong>Nhiều điểm</strong> để tối ưu thứ tự ghé cho một danh sách giao hàng.
7. Mở <strong>Thuật toán</strong> để xem complexity, completeness, optimality và điều kiện của heuristic.

## Kiến trúc

~~~text
React + TypeScript + Leaflet + Recharts + Motion
                   │ REST /api/v1
                   ▼
FastAPI → cost/traffic/heuristic registries → 8 search runners
                   │
                   ├─ explanation + alternative-route engine
                   ├─ multi-stop optimizer
                   └─ backend/data/hcmc_delivery_osm_snapshot.json
~~~

Backend không dùng NetworkX cho search. Các thuật toán trả cùng một response contract để frontend dùng chung renderer cho trace và metrics.

React tải topology/geometry đúng một lần bằng `/graph?compact=true`. Khi đổi scenario, client chỉ lấy status cạnh từ `/traffic` rồi cập nhật màu đường theo các chunk `requestAnimationFrame`; full effect vẫn giữ nguyên nhưng không khóa main thread bằng cách parse và restyle toàn graph đồng bộ.

## Dataset và provenance

Runtime chỉ đọc file canonical:

<code>backend/data/hcmc_delivery_osm_snapshot.json</code>

Snapshot có bbox <code>[10.750, 106.665, 10.800, 106.715]</code> theo thứ tự south, west, north, east. Query nguồn chỉ lấy các trục <code>primary|secondary|tertiary</code> cùng link tương ứng và năm nhóm POI, vì vậy dataset không đại diện đầy đủ hẻm, đường nội bộ, turn restriction hay toàn bộ thành phố.

Dữ liệu do teammate scrape/import được giữ ở <code>backend/data-tmp/</code> và đã được git-ignore. Thư mục đó là input tạm cho bước migration, không phải dependency runtime. Pipeline chuẩn hóa:

~~~powershell
python scripts/import_hcmc_snapshot.py
~~~

Script đọc processed graph và raw Overpass export trong thư mục tạm, kiểm tra schema/direction/geometry/speed/risk, rồi ghi snapshot canonical vào <code>backend/data</code>. Sau khi snapshot đã tồn tại, backend và frontend vẫn chạy khi <code>data-tmp</code> không có mặt.

Phân tách nguồn dữ liệu:

- OSM snapshot: topology, coordinates, road/POI names, highway class, one-way tags, geometry và một phần maxspeed.
- Derived: contraction, POI connector, speed fallback theo road class và component membership.
- Synthetic educational layer: baseline congestion, scenario multipliers, flood/disruption flags, closures, risk và ETA.

Chi tiết schema, checksum, phép dựng speed và các giới hạn nằm trong [docs/DATASET.md](docs/DATASET.md). Điều khoản OSM/ODbL nằm trong [NOTICE.md](NOTICE.md).

## Cấu trúc project

~~~text
backend/                 FastAPI, algorithms, optimizers, tests, canonical datasets
frontend/                React/Vite UI, API adapter và Playwright tests
scripts/                 setup/dev/check + HCMC import pipeline
docs/                    report, API, dataset, rubric và demo script
README.md                hướng dẫn tổng quan
~~~

## Tài liệu

- [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md): báo cáo kỹ thuật.
- [docs/ALGORITHM_REFERENCE.md](docs/ALGORITHM_REFERENCE.md): nguyên lý và guarantee của thuật toán.
- [docs/API.md](docs/API.md): API contract.
- [docs/RUBRIC_CHECKLIST.md](docs/RUBRIC_CHECKLIST.md): mapping rubric sang evidence.
- [docs/DEMO_VIDEO_SCRIPT.md](docs/DEMO_VIDEO_SCRIPT.md): kịch bản video.
- [docs/DATASET.md](docs/DATASET.md): provenance, schema và data audit.

## Giới hạn sử dụng

Ứng dụng không có GPS, live traffic, trạng thái đơn hàng, năng lực phương tiện, turn-by-turn guidance hay đảm bảo an toàn. Basemap và snapshot có thể cũ hoặc thiếu; traffic, ETA và risk là ước lượng giáo dục deterministic. Không dùng output làm chỉ dẫn giao thông thực tế hoặc quyết định vận hành.
