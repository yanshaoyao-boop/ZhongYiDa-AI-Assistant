from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import upload, chat

app = FastAPI(title="ZhongYiDa AI Assistant API")

# Setup CORS
# Setup CORS (Task 7: Improved for security and browsers compatibility)
app.add_middleware(
    CORSMiddleware,
    # In production, specify actual domains. For local dev with credentials, 
    # we use set list instead of "*" to avoid browser rejections.
    allow_origin_regex="https?://.*", 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "ZhongYiDa AI Assistant API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
