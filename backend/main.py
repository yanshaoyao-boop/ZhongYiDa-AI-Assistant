from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os
from routers import upload, chat

load_dotenv()

app = FastAPI(title="ZhongYiDa AI Assistant API")

# 从环境变量读取 CORS 白名单，防止钍孔柯突破设置
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,          # 白名单模式，替代原来的全开regex
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # 只开放实际用到的方法
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(upload.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "ZhongYiDa AI Assistant API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
