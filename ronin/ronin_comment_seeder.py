# ronin_comment_seeder.py
# @RoninWords用：投稿直後に自分で付ける「1コメ目」の文章を作る（純粋関数のみ）
# 早期リプライでアルゴリズムに会話を認識させ、reachを伸ばす狙い。
# 実際の返信送信は ronin_threads_action.post_to_threads(reply_to_id=...) を使う。

# Threads APIの本文上限
MAX_LEN = 500

# 教えの投稿（既存400本）に付ける汎用の問いかけ。カウントで回す。
GENERIC_SEED_QUESTIONS = [
    "Which line hit hardest for you today? Drop it below. 👇",
    "Where does this show up in your life right now?",
    "Save this if you needed it today — and tell me why.",
    "One word: what does this teaching ask of you tomorrow?",
    "Agree, or does your experience say otherwise?",
]


def pick_generic_seed(count):
    """カウント(0始まり)で汎用の問いかけを順番に選ぶ（末尾を超えたら先頭へ）"""
    return GENERIC_SEED_QUESTIONS[count % len(GENERIC_SEED_QUESTIONS)]


def build_seed_comment(base, cta=""):
    """1コメ目の本文を作る。ベースの問いかけ＋（CTAサイクル時のみ）リンク行を連結する。"""
    text = base
    if cta:
        text = f"{base}\n\n{cta}"  # 2行空けてリンクを足す（本文には入れない）
    return text[:MAX_LEN]  # 念のため500字に丸める


# 6カテゴリ別の問いかけ。ronin_theme_classifier.classify_category が返すキー"1"〜"6"に対応。
# カテゴリが判定できた投稿には、汎用問いかけより刺さりやすいテーマ別の問いかけを出す。
THEME_SEED_QUESTIONS = {
    "1": [  # Discipline / habits（規律・習慣）
        "What's one habit you've kept even when you didn't feel like it?",
        "Discipline or motivation — which one actually gets you through today?",
        "What does your morning routine look like right now?",
        "Save this if your discipline needs a reminder today.",
        "What's the smallest habit that's made the biggest difference for you?",
    ],
    "2": [  # Resilience / adversity（逆境・打たれ強さ）
        "What's the hardest setback you've come back from?",
        "When did failing actually teach you something useful?",
        "What keeps you going when things get hard?",
        "Save this for the next time you want to quit.",
        "Tell me about a time you bounced back from something that broke you.",
    ],
    "3": [  # Focus / distraction（集中・誘惑）
        "What's stealing your focus most days?",
        "How do you protect your deep work time?",
        "Phone in another room — yes or no?",
        "Save this if your attention span needs a reset.",
        "What's your biggest distraction right now, honestly?",
    ],
    "4": [  # Stoic / mindset（ストイック・心の在り方）
        "What's something you can't control that you're still trying to control?",
        "How do you stay calm when everything feels chaotic?",
        "What would the stoic version of you do right now?",
        "Save this the next time anxiety takes the wheel.",
        "What's one thing you've learned to accept instead of fight?",
    ],
    "5": [  # Mastery / craft（熟達・鍛錬）
        "What craft are you slowly mastering, one rep at a time?",
        "How many years have you put into the thing you're best at?",
        "What does practice look like for you this week?",
        "Save this if you're in the boring middle of mastering something.",
        "What skill are you most proud of building from scratch?",
    ],
    "6": [  # Purpose / meaning（目的・意味）
        "What gives your days meaning right now?",
        "How do you know when you're living with purpose?",
        "What's your 'why' when things get hard?",
        "Save this if you're still searching for your ikigai.",
        "What would you do even if no one paid you for it?",
    ],
}


def pick_seed_question(count, theme_key):
    """カウント(0始まり)でテーマ別の問いかけを順番に選ぶ。
    theme_key が THEME_SEED_QUESTIONS に無ければ汎用問いかけ（pick_generic_seed）にフォールバックする。"""
    pool = THEME_SEED_QUESTIONS.get(theme_key)
    if not pool:
        return pick_generic_seed(count)
    return pool[count % len(pool)]
