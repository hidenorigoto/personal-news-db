"""後方互換性のための要約機能ラッパー

このモジュールは既存コードとの互換性を保つために残されています。
新しいコードでは news_assistant.ai.summarizer を直接使用してください。
"""

# 新しいAIモジュールから必要な機能をインポート
from .ai.summarizer import generate_summary
from .ai.exceptions import SummaryGenerationError

# 後方互換性のため、既存の関数とクラスをエクスポート
__all__ = ["generate_summary", "SummaryGenerationError"]
