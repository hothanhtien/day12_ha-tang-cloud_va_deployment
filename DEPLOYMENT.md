# Deployment Information

## Public URL
https://tien-lab.khoav4.com

## Platform
Self-hosted VPS with Docker Compose + Cloudflare Tunnel (cloudflared)

## Architecture
```
Internet → Cloudflare Tunnel (cloudflared) → Nginx → FastAPI (uvicorn) → Redis
```

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

## Environment Variables Set on Server
- `PORT`
- `ENVIRONMENT`
- `OPENAI_API_KEY`
- `AGENT_API_KEY`
- `REDIS_URL`
- `ALLOWED_ORIGINS`
- `DAILY_BUDGET_USD`
- `RATE_LIMIT_PER_MINUTE`
