# ronin_theme_classifier.py
# @RoninWords 投稿・返信テキストのテーマ分類（6カテゴリ）。
# ronin_reply_hunter.py（半自動リプ下書き）・ronin_reply_engine.py（自動リプ本体）・
# ronin_threads_action.py（自動投稿の1コメ目シード・CTA連動）の3箇所で同じ分類ロジックが
# 必要になったため、単一モジュールに切り出した。

# 投稿文に含まれる英語キーワード → どのカテゴリーか の対応表
# （ronin_comment_templates.py の6カテゴリ "1"〜"6" に合わせる）
KEYWORD_MAP = {
    "1": ["discipline", "habit", "routine", "consistency", "willpower", "consistent", "self-control", "show up"],  # 規律・習慣
    "2": ["fail", "failure", "struggle", "adversity", "setback", "quit", "hard time", "resilience", "bounce back"],  # 逆境・打たれ強さ
    "3": ["focus", "distraction", "distracted", "procrastinate", "attention", "deep work", "concentration", "noise"],  # 集中・誘惑
    "4": ["stoic", "stoicism", "mindset", "calm", "anxiety", "fear", "control", "acceptance", "let go"],  # ストイック・心の在り方
    "5": ["master", "mastery", "skill", "craft", "practice", "improve", "discipline of", "expertise", "reps"],  # 熟達・鍛錬
    "6": ["purpose", "meaning", "goal", "vision", "direction", "why", "ikigai", "mission", "calling"],  # 目的・意味
}


def classify_category(text):
    """本文から最も当てはまるカテゴリキー（"1"〜"6"）を返す。
    キーワードが一番多く当たったカテゴリを選ぶ。同点なら番号の若い方（辞書の順序どおり）。
    どのキーワードにも当たらなければ None。"""
    lowered = text.lower()
    best_key = None
    best_hits = 0
    for key, words in KEYWORD_MAP.items():
        hits = sum(1 for word in words if word.lower() in lowered)
        if hits > best_hits:
            best_key = key
            best_hits = hits
    return best_key
