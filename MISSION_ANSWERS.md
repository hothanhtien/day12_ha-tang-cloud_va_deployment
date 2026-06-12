# Day 12 Lab - Mission Answers

**Student Name:** Ha Tang  
**Date:** 2026-06-12

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `01-localhost-vs-production/develop/app.py`

1. **Hardcoded API key** — `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` và `DATABASE_URL` hardcode thẳng trong code → push lên GitHub là lộ key ngay.
2. **Hardcoded host `localhost`** — `host="localhost"` trong `uvicorn.run()` → container không nhận traffic từ bên ngoài.
3. **Hardcoded port** — `port=8000` không đọc từ env var → trên Railway/Render, platform inject `PORT` khác nhau.
4. **Debug mode luôn bật** — `DEBUG = True` và `reload=True` → chậm, tiềm ẩn lỗ hổng bảo mật trong production.
5. **Print secret ra log** — `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` → lộ secret trong log files.
6. **Không có health check endpoint** — nếu agent crash, platform không biết để tự restart container.
7. **Không xử lý graceful shutdown** — process bị kill đột ngột, request đang xử lý bị mất.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Tại sao quan trọng? |
|---------|---------|------------|---------------------|
| Config | Hardcode trực tiếp trong code | Đọc từ env vars qua `os.getenv()` | Không lộ secret, thay đổi config không cần sửa code |
| Health check | Không có | `GET /health` + `GET /ready` | Platform biết khi nào restart container, load balancer biết khi nào route traffic |
| Logging | `print()` | JSON structured logging (`{"ts":...,"lvl":...,"msg":...}`) | Dễ parse bằng log aggregator (Datadog, CloudWatch), tìm lỗi nhanh hơn |
| Shutdown | Đột ngột (kill process) | Graceful — xử lý xong request hiện tại mới tắt | Không mất request đang chạy, data không bị corrupt |
| Host binding | `localhost` (chỉ local) | `0.0.0.0` (accept mọi interface) | Container cần lắng nghe trên tất cả interface mới nhận traffic từ ngoài |
| Port | Hardcode `8000` | Đọc từ `PORT` env var | Cloud platform inject PORT khác nhau tùy environment |

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile questions (`02-docker/develop/Dockerfile`)

1. **Base image là gì?** — `python:3.11` (full Python distribution, ~1 GB)
2. **Working directory là gì?** — `/app`
3. **Tại sao COPY requirements.txt trước?** — Docker build theo từng layer. Nếu chỉ thay đổi code (không thay đổi requirements.txt), Docker dùng lại layer cache của bước `pip install` → build nhanh hơn nhiều.
4. **CMD vs ENTRYPOINT khác nhau thế nào?** — `CMD` có thể bị override khi `docker run <image> <command>`, còn `ENTRYPOINT` là lệnh cố định, args truyền vào được append thêm vào sau. `CMD` dùng khi muốn default command dễ thay, `ENTRYPOINT` dùng khi container là một executable cụ thể.

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)

- **Stage 1 (builder)** làm gì? — Cài `gcc`, `libpq-dev` và toàn bộ Python dependencies bằng `pip install --user`. Stage này có đầy đủ build tools.
- **Stage 2 (runtime)** làm gì? — Chỉ copy `site-packages` từ stage 1 sang image `python:3.11-slim` sạch. Không có build tools, không có cache pip.
- **Tại sao image nhỏ hơn?** — Image runtime chỉ chứa Python slim + packages đã compile, không chứa `gcc`, `apt cache`, pip cache → nhỏ hơn đáng kể. Thêm vào đó, `python:3.11-slim` nhỏ hơn `python:3.11` vì bỏ nhiều package hệ thống không cần thiết.

### Exercise 2.4: Docker Compose Architecture

```
                    ┌─────────────────────────────────┐
Internet ──────────►│  Nginx (port 80)                │
                    │  Reverse proxy / Load Balancer   │
                    └───────────────┬─────────────────┘
                                    │ proxy_pass
                    ┌───────────────▼─────────────────┐
                    │  FastAPI Agent (port 8000)       │
                    │  uvicorn                         │
                    └───────────────┬─────────────────┘
                                    │ redis://redis:6379
                    ┌───────────────▼─────────────────┐
                    │  Redis (port 6379)               │
                    │  Session / Rate limit store      │
                    └─────────────────────────────────┘
```

Services được start: **nginx**, **agent** (FastAPI), **redis**.  
Chúng communicate qua Docker internal network tên `app-network`.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Deployment

- **Platform:** Self-hosted VPS + Docker Compose + Cloudflare Tunnel
- **Public URL:** https://tien-lab.khoav4.com
- **Status:** Live ✅

Health check response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 792.2,
  "checks": {"llm": "openai"}
}
```

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| | `railway.toml` | `render.yaml` |
|---|---|---|
| Format | TOML | YAML |
| Build command | `[build] builder = "DOCKERFILE"` | `buildCommand` field |
| Start command | `[deploy] startCommand` | `startCommand` field |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Env vars | Set qua CLI/dashboard | Có thể định nghĩa trong file với `envVars` |
| Auto-deploy | Mặc định từ GitHub | Cần connect repo trong dashboard |

---

## Part 4: API Security

### Exercise 4.1–4.3: Test results

**Test 1 — Không có API key (expect 401):**
```bash
curl -X POST https://tien-lab.khoav4.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```
✅ Trả về 401 đúng như kỳ vọng.

**Test 2 — Có API key (expect 200):**
```bash
curl -X POST https://tien-lab.khoav4.com/ask \
  -H "X-API-Key: tien" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
```json
{
  "question": "What is Docker?",
  "answer": "Docker là một nền tảng mã nguồn mở cho phép phát triển, vận chuyển và chạy các ứng dụng trong các container...",
  "model": "gpt-4o-mini",
  "timestamp": "2026-06-12T08:52:43.994723+00:00"
}
```
✅ Trả về 200 với câu trả lời từ OpenAI thật.

**Test 3 — Rate limit (5 requests liên tiếp):**
```
200
200
200
200
200
```
✅ Tất cả pass (rate limit = 20 req/min, 5 requests chưa đủ để trigger).

**Rate Limiting Algorithm:** Sliding Window Counter  
- Mỗi user (theo API key prefix) có 1 deque timestamps  
- Mỗi request: loại timestamps cũ hơn 60 giây, đếm còn lại  
- Vượt `RATE_LIMIT_PER_MINUTE` → HTTP 429 với header `Retry-After: 60`

### Exercise 4.4: Cost guard implementation

Cost guard trong `06-lab-complete/app/main.py` dùng in-memory tracking:

```python
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:          # Reset mỗi ngày
        _daily_cost = 0.0
        _cost_reset_day = today
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted.")
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    _daily_cost += cost
```

**Daily cost hiện tại:** $0.0001 / $5.00 budget (0.0% used)

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

Hai endpoints đã implemented trong `06-lab-complete/app/main.py`:

```python
@app.get("/health")          # Liveness probe
def health():
    return {"status": "ok", "uptime_seconds": ..., "checks": {"llm": "openai"}}

@app.get("/ready")           # Readiness probe
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}
```

**Tại sao cần 2 endpoints khác nhau?**  
- `/health` (liveness): container còn sống không? Fail → platform restart container  
- `/ready` (readiness): có sẵn sàng nhận traffic chưa? Fail → load balancer ngừng route vào instance này (dùng khi deploy mới, warm-up)

### Exercise 5.2: Graceful shutdown

```python
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)
```

**Flow:** Platform gửi `SIGTERM` → handler log event → uvicorn hoàn thành requests đang xử lý → tắt.

### Exercise 5.3–5.5: Stateless design với Redis

**Vấn đề khi có nhiều instances:**
- Instance 1: User A gửi request 1 → session lưu trong memory của instance 1  
- Instance 2: User A gửi request 2 → không có session → bug!

**Giải pháp (`05-scaling-reliability/production/app.py`):**
```python
def save_session(session_id: str, data: dict, ttl_seconds=3600):
    _redis.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

def load_session(session_id: str) -> dict:
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

Bất kỳ instance nào cũng đọc được session từ Redis → scale ngang an toàn.

**Metrics thực tế từ production:**
```json
{
  "uptime_seconds": 797.2,
  "total_requests": 22,
  "error_count": 0,
  "daily_cost_usd": 0.0001,
  "budget_used_pct": 0.0
}
```
