from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os
from routers import upload, chat, auth, staff, settings, chat_logs, client_logs, notices

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_methods=["GET", "POST", "DELETE"],  # 只开放实际用到的方法
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(settings.router)
app.include_router(auth.router)
app.include_router(staff.router)
app.include_router(upload.router)
app.include_router(client_logs.router)
app.include_router(chat.router)
app.include_router(chat_logs.router)
app.include_router(notices.router)

@app.get("/")
def read_root():
    return {"message": "ZhongYiDa AI Assistant API is running"}



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
