import io
import os
from urllib.parse import urlparse

import pypdf
import requests
from bs4 import BeautifulSoup
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from . import summary as summary_module
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="News Assistant API")

app.state.DATA_DIR = "data"
os.makedirs(app.state.DATA_DIR, exist_ok=True)


def get_extension_from_content_type(content_type: str, url: str = "") -> str:
    mime = content_type.split(";")[0].strip().lower() if content_type else ""
    mime_map = {
        "text/html": "html",
        "application/xhtml+xml": "html",
        "application/json": "json",
        "application/xml": "xml",
        "text/xml": "xml",
        "text/plain": "txt",
        "application/pdf": "pdf",
    }
    if mime in mime_map:
        return mime_map[mime]
    if not mime:
        # URLから拡張子を抽出
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        allowed = {"html", "htm", "pdf", "txt", "json", "xml"}
        if ext in allowed:
            return "html" if ext == "htm" else ext
        return "html"
    if "/" in mime:
        return mime.split("/")[-1]
    return "bin"


def extract_title_from_html(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        return str(title_tag.text.strip())
    return ""


def extract_title_from_pdf(content: bytes) -> str:
    try:
        with io.BytesIO(content) as pdf_io:
            reader = pypdf.PdfReader(pdf_io)
            if reader.metadata and reader.metadata.title:
                return str(reader.metadata.title)
    except Exception:
        pass
    return ""


def extract_text_from_html(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    # <body>タグ優先、なければ全テキスト
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)
    return text


def extract_text_from_pdf(content: bytes) -> str:
    try:
        with io.BytesIO(content) as pdf_io:
            reader = pypdf.PdfReader(pdf_io)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def extract_text_from_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


@app.post("/api/articles/", response_model=schemas.Article)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)) -> models.Article:
    """記事を新規登録するAPIエンドポイント。"""
    # URLのコンテンツ取得
    try:
        resp = requests.get(article.url, timeout=10)
        resp.raise_for_status()
        content = resp.content
        content_type = resp.headers.get("Content-Type", "")
        ct = content_type
        url = article.url
        ext = get_extension_from_content_type(
            ct,
            url
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch content: {e}"
        ) from e

    # タイトル自動抽出
    auto_title = ""
    if ext == "html":
        auto_title = extract_title_from_html(content)
    elif ext == "pdf":
        auto_title = extract_title_from_pdf(content)
    # title優先順位: 自動抽出 > リクエストボディ
    final_title = auto_title if auto_title else article.title

    # 本文抽出
    extracted_text = ""
    if ext == "html":
        extracted_text = extract_text_from_html(content)
    elif ext == "pdf":
        extracted_text = extract_text_from_pdf(content)
    elif ext == "txt":
        extracted_text = extract_text_from_txt(content)
    # それ以外は空文字

    # 要約生成
    summary = ""
    if extracted_text.strip():
        try:
            summary = summary_module.generate_summary(extracted_text)
        except Exception:
            summary = ""

    db_article = models.Article(url=article.url, title=final_title, summary=summary)
    db.add(db_article)
    try:
        db.commit()
        db.refresh(db_article)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="URL already registered"
        ) from e

    # ファイル名生成: {日付}_{記事ID}.{拡張子}
    date_str = db_article.created_at.strftime("%Y%m%d")
    filename = f"{date_str}_{db_article.id}.{ext}"
    filepath = os.path.join(app.state.DATA_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    return db_article


@app.get("/api/articles/", response_model=schemas.ArticleList)
def read_articles(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> dict[str, list[models.Article]]:
    """記事一覧を取得するAPIエンドポイント。"""
    articles = db.query(models.Article).offset(skip).limit(limit).all()
    return {"articles": articles}


@app.get("/api/articles/{article_id}", response_model=schemas.Article)
def read_article(article_id: int, db: Session = Depends(get_db)) -> models.Article:
    """個別記事を取得するAPIエンドポイント。"""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
