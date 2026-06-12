# Deployment Information

## Public URL
https://tien-lab.khoav4.com

## Platform
Self-hosted VPS with Docker Compose + Cloudflare Tunnel (cloudflared)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

  Developer                GitHub                    VPS Server
  ─────────                ──────                    ──────────
  git push ──────────────► main branch
                                │
                                │  (manual: git pull on server)
                                ▼
                           ┌─────────────────────────────────────┐
                           │           VPS (HP Server)           │
                           │                                     │
                           │  docker compose up -d               │
                           │  ┌──────────┐  ┌────────────────┐  │
                           │  │  Nginx   │  │  FastAPI       │  │
                           │  │ :80/:443 │◄─│  (uvicorn)     │  │
                           │  └──────────┘  │  :8000         │  │
                           │       ▲        └───────┬────────┘  │
                           │       │                │           │
                           │  ┌────┴───────┐  ┌────▼────────┐  │
                           │  │ cloudflared│  │   Redis     │  │
                           │  │  tunnel    │  │   :6379     │  │
                           │  └────┬───────┘  └─────────────┘  │
                           └───────┼─────────────────────────────┘
                                   │ outbound tunnel
                                   ▼
                           Cloudflare Network
                                   │
                                   ▼
                    https://tien-lab.khoav4.com
                                   │
                                   ▼
                             User / Client
```

**Luồng request:**
1. User gửi request tới `https://tien-lab.khoav4.com`
2. Cloudflare DNS → Cloudflare Network (TLS terminated)
3. Cloudflare → `cloudflared` daemon trên server (outbound tunnel, không cần mở port)
4. `cloudflared` → Nginx (`:80`)
5. Nginx reverse proxy → FastAPI uvicorn (`:8000`)
6. FastAPI xử lý: auth → rate limit → cost guard → OpenAI → response
7. Session/state lưu Redis (stateless-ready)

---

## Test Commands & Results

### Health Check
```bash
curl https://tien-lab.khoav4.com/health
```
**Result:**
```json
{"status":"ok","version":"1.0.0","environment":"production","uptime_seconds":792.2,"total_requests":21,"checks":{"llm":"openai"},"timestamp":"2026-06-12T08:52:39.687847+00:00"}
```

### Readiness Probe
```bash
curl https://tien-lab.khoav4.com/ready
```
**Result:**
```json
{"ready":true}
```

### API Test — No Key (expect 401)
```bash
curl -X POST https://tien-lab.khoav4.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
**Result:**
```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### API Test — With Key (expect 200)
```bash
curl -X POST https://tien-lab.khoav4.com/ask \
  -H "X-API-Key: tien" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
**Result:**
```json
{
  "question": "What is Docker?",
  "answer": "Docker là một nền tảng mã nguồn mở cho phép phát triển, vận chuyển và chạy các ứng dụng trong các container. Container giúp đóng gói tất cả các thành phần cần thiết của ứng dụng (bao gồm mã nguồn, thư viện và các phụ thuộc) để chạy nhất quán trên bất kỳ môi trường nào.",
  "model": "gpt-4o-mini",
  "timestamp": "2026-06-12T08:52:43.994723+00:00"
}
```

### Metrics (protected)
```bash
curl https://tien-lab.khoav4.com/metrics \
  -H "X-API-Key: tien"
```
**Result:**
```json
{
  "uptime_seconds": 797.2,
  "total_requests": 22,
  "error_count": 0,
  "daily_cost_usd": 0.0001,
  "daily_budget_usd": 5.0,
  "budget_used_pct": 0.0
}
```

### Rate Limit Test (5 consecutive requests)
```bash
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST https://tien-lab.khoav4.com/ask \
    -H "X-API-Key: tien" \
    -H "Content-Type: application/json" \
    -d '{"question": "test '$i'"}';
done
```
**Result:**
```
200
200
200
200
200
```

---

## Screenshots
- [Docker build](06-lab-complete/screenshots/image1_build.jpg)
- [Docker ps (containers running)](06-lab-complete/screenshots/image2_docker_ps.jpg)
- [Cloudflare Tunnel](06-lab-complete/screenshots/image_cloudflare.jpg)
- [UI running](06-lab-complete/screenshots/image_UI.jpg)
- [Curl test results](06-lab-complete/screenshots/image_test_curl.jpg)

---

## Environment Variables Set on Server
- `PORT`
- `ENVIRONMENT`
- `OPENAI_API_KEY`
- `AGENT_API_KEY`
- `REDIS_URL`
- `ALLOWED_ORIGINS`
- `DAILY_BUDGET_USD`
- `RATE_LIMIT_PER_MINUTE`
