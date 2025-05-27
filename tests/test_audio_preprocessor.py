"""音声読み上げ用テキスト前処理のテスト"""

from news_assistant.content.audio_preprocessor import AudioTextPreprocessor


class TestAudioTextPreprocessor:
    """AudioTextPreprocessorのテスト"""

    def test_remove_visual_instructions(self) -> None:
        """視覚的指示の削除テスト"""
        text = "詳細はこちらをクリックしてください。下記のリンクを参照してください。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        assert "こちらをクリック" not in result
        assert "下記のリンク" not in result

    def test_process_urls(self) -> None:
        """URL処理のテスト"""
        text = "詳細は https://example.com を参照してください。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        assert "リンク" in result
        assert "https://example.com" not in result

    def test_convert_symbols(self) -> None:
        """記号変換のテスト"""
        text = "価格は¥1,000です。※注意事項を確認してください。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        assert "円" in result
        assert "なお" in result
        assert "¥" not in result
        assert "※" not in result

    def test_normalize_parentheses(self) -> None:
        """括弧の正規化テスト"""
        text = "これは【重要】な内容です。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        assert "（重要）" in result
        assert "【" not in result
        assert "】" not in result

    def test_remove_redundant_punctuation(self) -> None:
        """冗長な句読点の削除テスト"""
        text = "これは、、、重要です。。。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        assert "、、、" not in result
        assert "。。。" not in result

    def test_fix_spacing(self) -> None:
        """スペースの修正テスト"""
        text = "これは    重要な    内容です。"
        result = AudioTextPreprocessor.preprocess_for_audio(text)
        # 複数スペースが単一スペースに
        assert "    " not in result

    def test_complex_text(self) -> None:
        """複雑なテキストの総合テスト"""
        text = """
        詳細は下記のリンクをクリックしてください。
        https://example.com/article/123

        価格：¥5,000（税込）
        ※送料は別途必要です。

        【重要】お申し込みは、、、こちらから。。。
        """
        result = AudioTextPreprocessor.preprocess_for_audio(text)

        # 視覚的指示が削除されている
        assert "下記のリンク" not in result
        assert "クリック" not in result

        # URLが処理されている
        assert "https://example.com" not in result
        assert "リンク" in result

        # 記号が変換されている
        assert "円" in result
        assert "¥" not in result
        assert "なお" in result
        assert "※" not in result

        # 括弧が正規化されている
        assert "（重要）" in result
        assert "【" not in result

        # 冗長な句読点が削除されている
        assert "、、、" not in result
        assert "。。。" not in result

    def test_empty_text(self) -> None:
        """空テキストの処理テスト"""
        result = AudioTextPreprocessor.preprocess_for_audio("")
        assert result == ""

    def test_none_safety(self) -> None:
        """None入力への対応テスト"""
        # 空文字列として処理されることを確認
        result = AudioTextPreprocessor.preprocess_for_audio("")
        assert result == ""
