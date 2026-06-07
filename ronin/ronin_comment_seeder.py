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
