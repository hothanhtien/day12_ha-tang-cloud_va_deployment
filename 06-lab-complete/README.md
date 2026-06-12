# Lab 12 — Complete Production Agent

Kết hợp TẤT CẢ những gì đã học trong 1 project hoàn chỉnh.

## Kiến Trúc

```
Internet
   │
   ▼
Cloudflare (tien-lab.khoav4.com)
   │
   ▼
cloudflared  ← tunnel, không cần public IP
   │
   ▼
nginx:80     ← reverse proxy + serve UI
   │
   ├── GET  /          → index.html (UI chat)
   ├── POST /ask       → backend:8000
   ├── GET  /health    → backend:8000
   └── GET  /ready     → backend:8000
          │
          ▼
      backend:8000     ← FastAPI agent
          │
          ▼
       redis:6379      ← rate limit, cost guard
```

---

## Checklist

- [x] Dockerfile (multi-stage, < 500 MB, non-root)
- [x] docker-compose.yml (backend + redis + nginx + cloudflared)
- [x] UI chat (`index.html`)
- [x] Health check endpoint (`GET /health`)
- [x] Readiness endpoint (`GET /ready`)
- [x] API Key authentication
- [x] Rate limiting (20 req/min)
- [x] Cost guard ($5/day)
- [x] Config từ environment variables
- [x] Structured JSON logging
- [x] Graceful shutdown
- [x] Redis volume (data không mất khi restart)
- [x] Public URL qua Cloudflare Tunnel

---

## Cấu Trúc

```
06-lab-complete/
├── app/
│   ├── main.py         # FastAPI app — auth, rate limit, cost guard
│   └── config.py       # 12-factor config từ env vars
├── index.html          # UI chat
├── Dockerfile          # Multi-stage build
├── docker-compose.yml  # backend + redis + nginx + cloudflared
├── .env.example        # Template — copy thành .env.local
├── .dockerignore
└── requirements.txt

../nginx/
└── nginx.conf          # Reverse proxy config

../cloudflared/
├── config.yml          # Tunnel config (tien-lab.khoav4.com)
└── *.json              # Credentials (KHÔNG commit lên git)
```

---

## Deploy Lên Server

### Bước 1 — Clone repo

```bash
git clone <repo-url>
cd day12_ha-tang-cloud_va_deployment/06-lab-complete
```

### Bước 2 — Tạo file `.env.local`

```bash
# Phải đứng trong 06-lab-complete/ thì cp mới tìm thấy .env.example
cd 06-lab-complete
cp .env.example .env.local
nano .env.local
```

> File `.env.local` phải nằm **ngay trong `06-lab-complete/`** cùng cấp với `docker-compose.yml`, vì compose đọc `env_file` theo working directory của file compose, không phải build context.

Sửa 3 giá trị bắt buộc:

```env
OPENAI_API_KEY=sk-...              # lấy từ platform.openai.com
AGENT_API_KEY=key-ban-tu-dat       # tự đặt, dùng để nhập vào UI
JWT_SECRET=<openssl rand -hex 32>  # chuỗi random
```

### Bước 3 — Thêm Cloudflare credentials

```bash
# Copy file JSON credentials vào thư mục cloudflared/
# (lấy từ Cloudflare Dashboard khi tạo tunnel)
cp ~/c2235da8-*.json ../cloudflared/
```

### Bước 4 — Build và chạy

```bash
docker compose up -d --build
```

### Bước 5 — Kiểm tra

```bash
# Xem logs
docker compose logs -f

# Ping health
curl https://tien-lab.khoav4.com/health

# Test API
curl https://tien-lab.khoav4.com/ask \
  -X POST \
  -H "X-API-Key: key-ban-tu-dat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

### Bước 6 — Mở UI

Truy cập **https://tien-lab.khoav4.com** → nhập `AGENT_API_KEY` → chat.

---

## Lệnh Hữu Ích

```bash
# Xem logs từng service
docker compose logs -f backend
docker compose logs -f cloudflared

# Restart một service
docker compose restart backend

# Dừng toàn bộ
docker compose down

# Dừng và xóa data Redis
docker compose down -v
```

---

## Kiểm Tra Production Readiness

```bash
python check_production_ready.py
```
