"""
LLM wrapper — Tự gọi OpenAI nếu có API key, fallback về mock nếu không.

- Có OPENAI_API_KEY → gọi OpenAI thật qua openai SDK
- Không có key hoặc lỗi → trả mock response (giữ nguyên logic cũ để lab offline)
"""
import os
import time
import random
import logging

logger = logging.getLogger(__name__)


# ── Mock responses (fallback khi không có API key) ───────────
MOCK_RESPONSES = {
    "default": [
        "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
        "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
        "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
    ],
    "docker": ["Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"],
    "deploy": ["Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được."],
    "health": ["Agent đang hoạt động bình thường. All systems operational."],
}


# ── OpenAI client (lazy init) ───────────────────────────────
_openai_client = None


def _get_openai_client():
    """Tạo OpenAI client 1 lần, cache lại."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _call_openai(question: str) -> str:
    """Gọi OpenAI Chat Completions API."""
    client = _get_openai_client()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Bạn là một AI agent hữu ích, trả lời ngắn gọn bằng tiếng Việt."},
            {"role": "user", "content": question},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ── Public API ───────────────────────────────────────────────
def ask(question: str, delay: float = 0.1) -> str:
    """
    Gọi LLM. Ưu tiên:
      1. OpenAI thật (nếu OPENAI_API_KEY có trong env)
      2. Mock response (fallback)
    """
    if os.getenv("OPENAI_API_KEY"):
        try:
            return _call_openai(question)
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return f"⚠️ Lỗi gọi OpenAI: {type(e).__name__}: {e}. (Đang dùng mock fallback.)"

    # ── Mock fallback (giữ nguyên logic cũ) ──
    time.sleep(delay + random.uniform(0, 0.05))

    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str):
    """
    Mock streaming — yield từng token.
    (Nếu muốn streaming OpenAI thật, dùng openai client.stream())
    """
    response = ask(question)
    words = response.split()
    for word in words:
        time.sleep(0.05)
        yield word + " "
