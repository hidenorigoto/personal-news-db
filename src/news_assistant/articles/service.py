"""記事関連のビジネスロジック"""

import logging
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..content import ContentProcessor
from ..core import ArticleNotFoundError, ContentProcessingError, DatabaseError
from ..speech import SpeechService
from .models import Article
from .schemas import ArticleCreate, ArticleUpdate

logger = logging.getLogger(__name__)


class ArticleService:
    """記事管理サービス"""

    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: ファイル保存ディレクトリ
        """
        self.content_processor = ContentProcessor(data_dir)
        self.speech_service = SpeechService()

    async def create_article_with_audio(self, db: Session, article_data: ArticleCreate) -> Article:
        """記事を作成し、音声も生成"""
        # まず記事を作成
        article = self.create_article(db, article_data)

        # 音声データを生成
        try:
            await self._generate_article_audio(article)
        except Exception as e:
            logger.error(f"Failed to generate audio for article {article.id}: {e}")
            # 音声生成に失敗しても記事作成は成功とする

        return article

    def create_article(self, db: Session, article_data: ArticleCreate) -> Article:
        """記事を作成"""
        try:
            # まず記事をDBに保存（IDを取得するため）
            db_article = Article(
                url=str(article_data.url), title=article_data.title, summary=""  # 後で更新
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
                    generate_summary_flag=True,
                )

                # 処理結果で記事を更新
                db_article.title = str(processed_content.title)  # type: ignore[assignment]
                db_article.summary = str(processed_content.summary)  # type: ignore[assignment]
                db.commit()
                db.refresh(db_article)

                # 音声データを生成（バックグラウンドで実行）
                # 注: 音声生成は別途バックグラウンドタスクとして実行する必要がある
                logger.info(f"Article {db_article.id} created, audio generation will be performed separately")

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
                details={"url": str(article_data.url)},
            ) from e

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
    def get_articles(db: Session, skip: int = 0, limit: int = 100) -> tuple[list[Article], int]:
        """記事一覧を取得（ページネーション対応）"""
        total = db.query(Article).count()
        articles = (
            db.query(Article).order_by(Article.created_at.desc()).offset(skip).limit(limit).all()
        )
        return articles, total

    @staticmethod
    def update_article(db: Session, article_id: int, article_data: ArticleUpdate) -> Article:
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
                details={"article_id": article_id},
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
                details={"article_id": article_id},
            ) from e

    async def _generate_article_audio(self, article: Article) -> None:
        """記事の音声データを生成（バックグラウンド処理）"""
        try:
            # 要約音声を生成
            if article.summary:
                summary_path = self.speech_service.generate_article_audio_path(
                    article_id=int(article.id), content_type="summary"
                )
                summary_response = await self.speech_service.text_to_speech_with_template(
                    text=str(article.summary),
                    article_title=str(article.title),
                    content_type="要約",
                    output_path=summary_path,
                )

                if summary_response.success:
                    logger.info(f"要約音声生成完了: 記事ID {article.id}")
                else:
                    logger.error(f"要約音声生成失敗: 記事ID {article.id}, エラー: {summary_response.error_message}")

            # 本文音声を生成（音声用前処理済みファイルを優先）
            audio_content_path = Path(self.content_processor.data_dir) / "raw" / f"article_{article.id}_audio.txt"
            raw_content_path = Path(self.content_processor.data_dir) / "raw" / f"article_{article.id}.txt"

            content_text = None
            # 音声用前処理済みファイルが存在すればそれを使用、なければ生のテキストを使用
            if audio_content_path.exists():
                content_text = audio_content_path.read_text(encoding='utf-8')
                logger.info(f"音声用前処理済みテキストを使用: 記事ID {article.id}")
            elif raw_content_path.exists():
                content_text = raw_content_path.read_text(encoding='utf-8')
                logger.info(f"生のテキストを使用: 記事ID {article.id}")

            if content_text:
                # テキストが長すぎる場合は最初の9000文字に制限（テンプレートヘッダー分の余裕を残す）
                if len(content_text) > 9000:
                    content_text = content_text[:9000] + "...（以下省略）"
                    logger.warning(f"本文が長すぎるため、最初の9000文字のみ音声化します: 記事ID {article.id}")

                full_audio_path = self.speech_service.generate_article_audio_path(
                    article_id=int(article.id), content_type="full"
                )
                full_response = await self.speech_service.text_to_speech_with_template(
                    text=content_text,
                    article_title=str(article.title),
                    content_type="本文",
                    output_path=full_audio_path,
                )

                if full_response.success:
                    logger.info(f"本文音声生成完了: 記事ID {article.id}")
                else:
                    logger.error(f"本文音声生成失敗: 記事ID {article.id}, エラー: {full_response.error_message}")

        except Exception as e:
            logger.error(f"音声生成中にエラーが発生: 記事ID {article.id}, エラー: {e}")

    async def generate_article_audio_sync(self, article: Article) -> dict[str, bool]:
        """記事の音声データを同期的に生成"""
        results = {"summary": False, "full": False}

        try:
            # 要約音声を生成
            if article.summary:
                summary_path = self.speech_service.generate_article_audio_path(
                    article_id=int(article.id), content_type="summary"
                )
                summary_response = await self.speech_service.text_to_speech_with_template(
                    text=str(article.summary),
                    article_title=str(article.title),
                    content_type="要約",
                    output_path=summary_path,
                )
                results["summary"] = summary_response.success

            # 本文音声を生成（音声用前処理済みファイルを優先）
            audio_content_path = Path(self.content_processor.data_dir) / "raw" / f"article_{article.id}_audio.txt"
            raw_content_path = Path(self.content_processor.data_dir) / "raw" / f"article_{article.id}.txt"

            content_text = None
            if audio_content_path.exists():
                content_text = audio_content_path.read_text(encoding='utf-8')
                logger.info(f"音声用前処理済みテキストを使用（同期）: 記事ID {article.id}")
            elif raw_content_path.exists():
                content_text = raw_content_path.read_text(encoding='utf-8')
                logger.info(f"生のテキストを使用（同期）: 記事ID {article.id}")

            if content_text:

                # テキストが長すぎる場合は最初の9000文字に制限（テンプレートヘッダー分の余裕を残す）
                if len(content_text) > 9000:
                    content_text = content_text[:9000] + "...（以下省略）"
                    logger.warning(f"本文が長すぎるため、最初の9000文字のみ音声化します: 記事ID {article.id}")

                full_audio_path = self.speech_service.generate_article_audio_path(
                    article_id=int(article.id), content_type="full"
                )
                full_response = await self.speech_service.text_to_speech_with_template(
                    text=content_text,
                    article_title=str(article.title),
                    content_type="本文",
                    output_path=full_audio_path,
                )
                results["full"] = full_response.success

        except Exception as e:
            logger.error(f"音声生成中にエラーが発生: 記事ID {article.id}, エラー: {e}")

        return results
