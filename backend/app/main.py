from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine
from app.models import user, chapter, word, vocabulary, settings, exam

# 创建表
user.Base.metadata.create_all(bind=engine)
chapter.Base.metadata.create_all(bind=engine)
word.Base.metadata.create_all(bind=engine)
vocabulary.Base.metadata.create_all(bind=engine)
settings.Base.metadata.create_all(bind=engine)
exam.Base.metadata.create_all(bind=engine)

# 导入路由
from app.api import auth_router, chapters_router, words_router, vocabulary_router, settings_router, exams_router

# 创建应用
app = FastAPI(title="IELTS Vocabulary API", version="1.0.0")
settings = get_settings()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(chapters_router)
app.include_router(words_router)
app.include_router(vocabulary_router)
app.include_router(settings_router)
app.include_router(exams_router)


@app.get("/")
def root():
    return {
        "message": "IELTS Vocabulary API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        reload=True,
        host="0.0.0.0",
        port=8000
    )
