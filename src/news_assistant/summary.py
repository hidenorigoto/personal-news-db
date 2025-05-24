import os

import openai

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

PROMPT_TEMPLATE = (
    "以下のニュース記事を1000文字程度で、重要なポイントを網羅するように要約してください。\n---\n{content}"
)

class SummaryGenerationError(Exception):
    pass

def generate_summary(content: str, model: str = "gpt-3.5-turbo", max_tokens: int = 900) -> str:
    """
    OpenAI APIを使って記事本文から要約を生成する。

    Args:
        content (str): 記事本文
        model (str): 使用するOpenAIモデル
        max_tokens (int): 出力トークン上限
    Returns:
        str: 生成された要約
    Raises:
        SummaryGenerationError: API失敗時
    """
    if not OPENAI_API_KEY:
        raise SummaryGenerationError("OPENAI_API_KEYが設定されていません")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    prompt = PROMPT_TEMPLATE.format(content=content)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        content_ = response.choices[0].message.content
        if content_ is None:
            raise SummaryGenerationError("OpenAI APIのレスポンスにcontentが含まれていません")
        summary = content_.strip()
        return summary
    except Exception as e:
        raise SummaryGenerationError(f"OpenAI API要約生成失敗: {e}") from e
