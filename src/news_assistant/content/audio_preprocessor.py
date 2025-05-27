"""音声読み上げ用テキスト前処理"""
import re


class AudioTextPreprocessor:
    """音声読み上げ用にテキストを前処理するクラス"""

    # 除去または変換すべきパターン
    VISUAL_INSTRUCTIONS = [
        (r'下記のリンクをクリック', ''),
        (r'上記のリンクをクリック', ''),
        (r'こちらをクリック', ''),
        (r'詳細はこちら', ''),
        (r'下記のリンク', ''),
        (r'上記のリンク', ''),
        (r'→詳細を見る', ''),
        (r'▶.*?を見る', ''),
        (r'↓.*?はこちら', ''),
        (r'\[続きを読む\]', ''),
        (r'＞＞続きを読む', ''),
        (r'…続きを読む', ''),
        (r'続きはこちら.*?$', ''),
    ]

    # URL パターン
    URL_PATTERN = re.compile(
        r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+|'
        r'www\.[\w/:%#\$&\?\(\)~\.=\+\-]+',
        re.IGNORECASE
    )

    # 括弧内の注釈パターン
    ANNOTATION_PATTERN = re.compile(
        r'[（\(](?:写真|画像|図|表|グラフ|出典|引用|参照|クリックで拡大)[）\)]',
        re.IGNORECASE
    )

    # 記号の変換マップ
    SYMBOL_MAP = {
        '※': '、なお、',
        '★': '、',
        '☆': '、',
        '●': '、',
        '○': '、',
        '■': '、',
        '□': '、',
        '▼': '、',
        '▲': '、',
        '→': '、',
        '⇒': '、',
        '←': '、',
        '⇐': '、',
        '¥': '円',
        '￥': '円',
        # 康熙部首を通常の漢字に変換
        '⾦': '金',
        '⽰': '示',
        '⾨': '門',
        '⾷': '食',
        '⾺': '馬',
        '⿂': '魚',
        '⿃': '鳥',
        '⿓': '竜',
    }

    @classmethod
    def preprocess_for_audio(cls, text: str) -> str:
        """
        音声読み上げ用にテキストを前処理

        Args:
            text: 処理対象のテキスト

        Returns:
            前処理済みのテキスト
        """
        if not text:
            return text

        # 1. 視覚的な指示の除去
        processed_text = cls._remove_visual_instructions(text)

        # 2. URLの処理
        processed_text = cls._process_urls(processed_text)

        # 3. 画像・図表の注釈を除去
        processed_text = cls._remove_annotations(processed_text)

        # 4. 記号の変換
        processed_text = cls._convert_symbols(processed_text)

        # 5. 箇条書きの整形
        processed_text = cls._format_bullet_points(processed_text)

        # 6. 括弧の正規化
        processed_text = cls._normalize_parentheses(processed_text)

        # 7. 冗長な句読点の削除
        processed_text = cls._remove_redundant_punctuation(processed_text)

        # 8. 連続する空白行の削減
        processed_text = cls._normalize_whitespace(processed_text)

        # 9. スペースの修正
        processed_text = cls._fix_spacing(processed_text)

        return processed_text.strip()

    @classmethod
    def _remove_visual_instructions(cls, text: str) -> str:
        """視覚的な指示を除去"""
        for pattern, replacement in cls.VISUAL_INSTRUCTIONS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @classmethod
    def _process_urls(cls, text: str) -> str:
        """URLを音声向けに処理"""
        # 文中のURLを「（リンク）」に置換
        text = cls.URL_PATTERN.sub('（リンク）', text)
        return text

    @classmethod
    def _remove_annotations(cls, text: str) -> str:
        """画像・図表の注釈を除去"""
        text = cls.ANNOTATION_PATTERN.sub('', text)
        return text

    @classmethod
    def _convert_symbols(cls, text: str) -> str:
        """記号を音声向けに変換"""
        for symbol, replacement in cls.SYMBOL_MAP.items():
            text = text.replace(symbol, replacement)
        return text

    @classmethod
    def _format_bullet_points(cls, text: str) -> str:
        """箇条書きを音声向けに整形"""
        lines = text.split('\n')
        formatted_lines = []
        bullet_count = 0

        for line in lines:
            stripped = line.strip()
            # 箇条書きの判定
            if stripped and any(stripped.startswith(marker) for marker in ['・', '•', '-', '*', '1.', '2.', '3.']):
                bullet_count += 1
                # 番号付きリストの場合
                if re.match(r'^\d+\.', stripped):
                    formatted_lines.append(stripped)
                else:
                    # 記号の箇条書きを番号付きに変換
                    content = re.sub(r'^[・•\-\*]\s*', '', stripped)
                    formatted_lines.append(f"{bullet_count}つ目、{content}")
            else:
                if stripped:  # 空行でない場合
                    bullet_count = 0  # 箇条書きの連続が終了
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """連続する空白行を正規化"""
        # 3行以上の連続空行を2行に
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 行末の空白を除去
        lines = [line.rstrip() for line in text.split('\n')]
        return '\n'.join(lines)

    @classmethod
    def _normalize_parentheses(cls, text: str) -> str:
        """括弧の正規化"""
        # 【】を（）に変換
        text = text.replace('【', '（').replace('】', '）')
        # 全角括弧に統一
        text = text.replace('(', '（').replace(')', '）')
        return text

    @classmethod
    def _remove_redundant_punctuation(cls, text: str) -> str:
        """冗長な句読点の削除"""
        # 連続する句読点を削減
        text = re.sub(r'、{2,}', '、', text)
        text = re.sub(r'。{2,}', '。', text)
        text = re.sub(r'[、。]{2,}', '。', text)
        return text

    @classmethod
    def _fix_spacing(cls, text: str) -> str:
        """スペースの修正"""
        # 連続するスペースを単一スペースに
        text = re.sub(r' {2,}', ' ', text)
        # 全角スペースも処理
        text = re.sub(r'　{2,}', '　', text)
        return text

    @classmethod
    def preprocess_for_summary_audio(cls, text: str) -> str:
        """
        要約用の音声前処理（より簡潔に）

        Args:
            text: 要約テキスト

        Returns:
            前処理済みのテキスト
        """
        # 要約は既に簡潔なので、最小限の処理のみ
        processed_text = cls._process_urls(text)
        processed_text = cls._convert_symbols(processed_text)
        processed_text = cls._normalize_whitespace(processed_text)

        return processed_text.strip()
