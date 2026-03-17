from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text
import uvicorn
import os
from routers import upload, chat, auth, staff, settings, chat_logs, client_logs, notices, tools, coach_quiz

load_dotenv()


def ensure_legacy_schema(engine):
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        notice_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(notices)")).fetchall()
        }
        if "created_by_id" not in notice_columns:
            connection.execute(text("ALTER TABLE notices ADD COLUMN created_by_id INTEGER"))
        if "created_by_name" not in notice_columns:
            connection.execute(text("ALTER TABLE notices ADD COLUMN created_by_name VARCHAR"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时确保数据库表结构同步
    from database import engine, Base
    import models.user, models.notice, models.chat_history # 显式引入以确保 Base 识别所有模型
    Base.metadata.create_all(bind=engine)
    ensure_legacy_schema(engine)
    print("Database tables synchronized.")
    yield
    # 应用强制关闭时，释放全局网络连接池
    from services.llm_client import close_client
    from services.tracking_service import close_browser
    try:
        await close_client()
        await close_browser()
        print("Closed LLM HTTP client connection pool and Playwright browser.")
    except Exception as e:
        print(f"Error closing LLM client/browser: {e}")

app = FastAPI(title="ZhongYiDa AI Assistant API", lifespan=lifespan)

# 从环境变量读取 CORS 白名单，防止非法跨域访问
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
if any("localhost" in o or "127.0.0.1" in o for o in ALLOWED_ORIGINS):
    print("⚠️  安全警告：CORS 白名单包含 localhost/127.0.0.1，生产环境请务必配置正式域名。")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,          # 白名单模式，替代原来的全开regex
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],  # 只开放实际用到的方法
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers with configurable prefix
API_PREFIX = os.getenv("API_PREFIX", "/api")
if API_PREFIX == "/": API_PREFIX = ""
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(staff.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)
app.include_router(client_logs.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(chat_logs.router, prefix=API_PREFIX)
app.include_router(notices.router, prefix=API_PREFIX)
app.include_router(tools.router, prefix=API_PREFIX)
app.include_router(coach_quiz.router, prefix=API_PREFIX)


@app.get("/")
def read_root():
    return {"message": "ZhongYiDa AI Assistant API is running"}



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
