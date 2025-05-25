"""記事関連のビジネスロジック"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..content import ContentProcessor
from ..core import ArticleNotFoundError, ContentProcessingError, DatabaseError
from .models import Article
from .schemas import ArticleCreate, ArticleUpdate


class ArticleService:
    """記事管理サービス"""

    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: ファイル保存ディレクトリ
        """
        self.content_processor = ContentProcessor(data_dir)

    @staticmethod
    def create_article_simple(db: Session, article_data: ArticleCreate) -> Article:
        """記事を作成（コンテンツ処理なし）"""
        try:
            db_article = Article(
                url=str(article_data.url),
                title=article_data.title,
                summary=article_data.summary or ""
            )
            db.add(db_article)
            db.commit()
            db.refresh(db_article)
            return db_article
        except IntegrityError as e:
            db.rollback()
            raise DatabaseError(
                "記事の作成に失敗しました。URLが既に登録されている可能性があります。",
                error_code="DUPLICATE_URL",
                details={"url": str(article_data.url)}
            ) from e

    def create_article_with_processing(self, db: Session, article_data: ArticleCreate) -> Article:
        """記事を作成（コンテンツ処理あり）"""
        try:
            # まず記事をDBに保存（IDを取得するため）
            db_article = Article(
                url=str(article_data.url),
                title=article_data.title,
                summary=""  # 後で更新
            )
            db.add(db_article)
            db.commit()
            db.refresh(db_article)

            # コンテンツ処理実行
            try:
                processed_content = self.content_processor.process_url(
                    url=str(article_data.url),
                    fallback_title=article_data.title,
                    article_id=int(db_article.id),
                    generate_summary_flag=True
                )

                # 処理結果で記事を更新
                db_article.title = str(processed_content.title)  # type: ignore[assignment]
                db_article.summary = str(processed_content.summary)  # type: ignore[assignment]
                db.commit()
                db.refresh(db_article)

            except ContentProcessingError as e:
                # コンテンツ処理に失敗した場合は元のデータで保存
                db_article.summary = str(article_data.summary or "")  # type: ignore[assignment]
                db.commit()
                db.refresh(db_article)
                # ログに記録（例外は再発生させない）
                import logging
                logging.warning(f"Content processing failed for article {db_article.id}: {e}")

            return db_article

        except IntegrityError as e:
            db.rollback()
            raise DatabaseError(
                "記事の作成に失敗しました。URLが既に登録されている可能性があります。",
                error_code="DUPLICATE_URL",
                details={"url": str(article_data.url)}
            ) from e

    @staticmethod
    def create_article(db: Session, article_data: ArticleCreate) -> Article:
        """記事を作成（デフォルト：コンテンツ処理なし）"""
        return ArticleService.create_article_simple(db, article_data)

    @staticmethod
    def get_article_by_id(db: Session, article_id: int) -> Article:
        """IDで記事を取得"""
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise ArticleNotFoundError(article_id)
        return article

    @staticmethod
    def get_article_by_url(db: Session, url: str) -> Article | None:
        """URLで記事を取得"""
        return db.query(Article).filter(Article.url == url).first()

    @staticmethod
    def get_articles(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Article], int]:
        """記事一覧を取得（ページネーション対応）"""
        total = db.query(Article).count()
        articles = (
            db.query(Article)
            .order_by(Article.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return articles, total

    @staticmethod
    def update_article(
        db: Session,
        article_id: int,
        article_data: ArticleUpdate
    ) -> Article:
        """記事を更新"""
        article = ArticleService.get_article_by_id(db, article_id)

        update_data = article_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)

        try:
            db.commit()
            db.refresh(article)
            return article
        except IntegrityError as e:
            db.rollback()
            raise DatabaseError(
                "記事の更新に失敗しました",
                error_code="UPDATE_FAILED",
                details={"article_id": article_id}
            ) from e

    @staticmethod
    def delete_article(db: Session, article_id: int) -> bool:
        """記事を削除"""
        article = ArticleService.get_article_by_id(db, article_id)

        try:
            db.delete(article)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise DatabaseError(
                "記事の削除に失敗しました",
                error_code="DELETE_FAILED",
                details={"article_id": article_id}
            ) from e
