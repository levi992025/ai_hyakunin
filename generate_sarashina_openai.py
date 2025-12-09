#!/usr/bin/env python3
import csv
import json
import time
import os

from openai import OpenAI

INPUT_CSV = "hyaku.csv"
OUTPUT_JSONL = "hyaku_sarashina_openai.jsonl"

MODEL_NAME = "gpt-4o-mini"  # 必要に応じて gpt-4o などに変更OK

SARASHINA_INSTRUCTIONS = """
あなたは「Sarashina先生」という、日本語学と古典文学に詳しい家庭教師です。
百人一首について正確で簡潔に説明します。余計な創作や、事実ではない推測は行いません。

次の百人一首について、次の3点を日本語で説明してください。
1. 作者の読み方（ひらがな）
2. 和歌全体の読み仮名（上の句・下の句を1行ずつ）
3. 和歌の要点（内容・情景）を、短い現代語で説明

説明は、落ち着いた丁寧な口調で、見出し付きで書いてください。
出力フォーマットの例：

【作者の読み方】
てんちてんのう

【和歌の読み仮名】
あきのたの かりほのいほの とまをあらみ
わがころもでは つゆにぬれつつ

【要点】
（ここに短い説明）
"""

USER_PROMPT_TEMPLATE = """次の百人一首について説明してください。

番号: {no}
作者: {author}
作者よみ（参考情報）: {yomi}

和歌（漢字）:
{waka}
{waka2}

和歌（ひらがな）:
{waka1h}
{waka2h}
"""


def is_valid_number(no_str: str) -> bool:
    no_str = no_str.strip()
    try:
        n = int(no_str)
    except ValueError:
        return False
    return 1 <= n <= 100


def call_openai(user_prompt: str) -> str:
    """OpenAI Responses API でテキスト生成。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("環境変数 OPENAI_API_KEY が設定されていません。")

    client = OpenAI(api_key=api_key)

    resp = client.responses.create(
        model=MODEL_NAME,
        instructions=SARASHINA_INSTRUCTIONS,
        input=user_prompt,
        max_output_tokens=512,
        temperature=0.4,
    )

    # テキスト全部をまとめて返すヘルパー
    return resp.output_text  # SDKに備わっているフィールド


def main():
    print(f"[OpenAI] model = {MODEL_NAME}")

    with open(INPUT_CSV, newline="", encoding="utf-8") as f_in, \
            open(OUTPUT_JSONL, "w", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)

        for row in reader:
            no_raw = (row.get("No") or "").strip()
            if not is_valid_number(no_raw):
                continue

            no = no_raw
            author = (row.get("author") or "").strip()
            yomi = (row.get("yomi") or "").strip()
            waka = (row.get("waka") or "").strip()
            waka2 = (row.get("waka2") or "").strip()
            waka1h = (row.get("waka1h") or "").strip()
            waka2h = (row.get("waka2h") or "").strip()

            user_prompt = USER_PROMPT_TEMPLATE.format(
                no=no,
                author=author,
                yomi=yomi,
                waka=waka,
                waka2=waka2,
                waka1h=waka1h,
                waka2h=waka2h,
            )

            print(f"[OpenAI] No.{no} {author} ...", flush=True)

            try:
                output_text = call_openai(user_prompt)
            except Exception as e:
                print(f"[ERROR OpenAI] No.{no}: {e}")
                output_text = ""

            record = {
                "instruction": SARASHINA_INSTRUCTIONS.strip(),
                "input": user_prompt,
                "output": output_text,
            }

            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

            time.sleep(0.3)  # レート制限対策（必要に応じ調整）


if __name__ == "__main__":
    main()
