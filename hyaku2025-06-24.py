import pandas as pd
import subprocess

# モデルをここで切り替えられる（小型モデルもOK）
OLLAMA_MODEL = "gemma3:1b"  # お好みで "phi3:3.8b" "tinyllama" "gemma3:1b" なども

# --- 起動メッセージ ---
print("🌸 Llamaせんせの 百人一首教室 はじまり〜♪ 🌸")
print("今日はどんなテーマで歌を学びたい？")

# --- メニュー表示 ---
menu = {
    '1': '春',
    '2': '夏',
    '3': '秋',
    '4': '冬',
    '5': '恋',
    '6': '夢'
}
for key, value in menu.items():
    print(f"{key}. {value}")

# --- 入力受付 ---
choice = input("気になるキーワード番号を入力してね (1-6)：").strip()
theme = menu.get(choice, '春')  # 無効な入力は「春」にデフォルト

# --- テーマとキーワードのマッピング ---
kigo = {
    '春': ['はる', 'さくら', 'うぐいす', 'わかな', 'はな', 'ながつき'],
    '夏': ['なつ', 'みそぎ'],
    '秋': ['あき', 'もみぢ', 'もみじ', 'かぜ', 'つき', 'しも', 'ちどり', 'ながめ'],
    '冬': ['ふゆ', 'ゆき', 'しも', 'さむ', 'ありあけ'],
    '恋': ['こひ', 'こい', '恋', 'したふ', 'わがせこ'],
    '夢': ['ゆめ', '夢', 'みる', 'まぼろし']
}

# --- データ読込 ---
try:
    df = pd.read_csv("hyaku.csv")
except Exception as e:
    print(f"CSVファイル読込エラー: {e}")
    exit()

# --- 和歌の分類 ---
season_poems = {season: [] for season in kigo}
for _, row in df.iterrows():
    try:
        waka = str(row['waka']) + str(row['waka2'])
        waka_h = str(row['waka1h']) + str(row['waka2h'])
        for season, keywords in kigo.items():
            if any(kw in waka_h for kw in keywords):
                season_poems[season].append({
                    'no': row['No'],
                    'poet': row['author'],
                    'yomi': row['yomi'],
                    'waka': row['waka'],
                    'waka2': row['waka2'],
                    'full_waka_k': waka,
                    'full_waka_h': waka_h
                })
                break
    except KeyError:
        continue  # 欠損データをスキップ

# --- Ollama問い合わせ関数（修正済） ---
def chat_with_ollama(message):
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=message,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # text=True なら input は str でOK
        )
        if result.returncode != 0:
            return f"Ollama エラー: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"実行時エラー: {e}"

# --- 出力 ---
print(f"\n🌸 今日のテーマは：{theme} 🌸\n")
poems = season_poems.get(theme, [])

if not poems:
    print("あら〜、そのテーマには和歌が見つからんかったわぁ…💦また別のテーマで試してな！")
else:
    poem = poems[0]  # 最初の1首だけ
    prompt = f"""
You are a poetic teacher named "Llama-sensei".
Please give a graceful explanation of the following waka poem, first in **English**, then in **Japanese**.

和歌（ひらがな）:
{poem['full_waka_h']}
作者: {poem['poet']}（読み: {poem['yomi']}）

Only respond in that order: Japanese → English.
Please do not mix both languages in the same sentence.
"""
    response = chat_with_ollama(prompt)
    print(f"【No.{poem['no']}】{poem['poet']} の和歌:")
    print(poem['full_waka_k'])
    print("【Llamaせんせ コメント】")
    print(response)
    print("-" * 40)
