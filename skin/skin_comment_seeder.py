# skin_comment_seeder.py
# skinアカウント用：投稿直後に自分で付ける「1コメ目」の文章を作る（純粋関数のみ）
# 早期リプライでアルゴリズムに会話を認識させ、reachを伸ばす狙い（roninで実証済み）。
# 実際の返信送信は skin_threads_action.post_to_threads(reply_to_id=...) を使う。

# Threads APIの本文上限
MAX_LEN = 500

# 深掘りコメントの先頭に付けるリード行
# （データ収集が「先頭50字一致」でテーマ判定するため、本文と同じ書き出しを避けて分析汚染を防ぐ）
DEEP_DIVE_LEAD = "ここから少し深掘り👇"

# human_post（完結型の投稿）に付ける汎用の問いかけ。カウントで回す。
GENERIC_SEED_QUESTIONS = [
    "この中で「これ自分かも」と思ったもの、あった？",
    "試したことがあるもの、あった？コメントで教えてね。",
    "一番ドキッとした行、どれだった？",
    "これ以外で手応えがあった習慣、あったらコメントで共有してね。",
    "明日からまず1つやるなら、どれにする？",
]

# 1コメ目の末尾に付けるCTA（行動のお願い）4型ローテーション
# 保存→フォロー→note誘導→リポストの順で回す（1日4投稿なので毎日全種類が1回ずつ出る）
CTA_SAVE = "🔖 読み返したくなったら保存しておいてね。1週間後に見返すと変化に気づきやすいです。"
CTA_FOLLOW = "毎日7時・12時・18時・21時に、肌を内側から整えるヒントを発信してます。フォローすると見逃しません🌱"
CTA_NOTE = "ここまで読んでくれたあなたへ。もっと詳しい完全版を無料noteにまとめてます👇\n{url}"
CTA_REPOST = "同じ悩みを持つ誰かに届くように、リポストしてもらえたら嬉しいです🙏"
# アフィリエイト誘導の文型（{name}=商品名 / {url}=アフィリエイトリンク）
# 「宣伝」感を抑えるため、実際に使っている前提のやわらかい言い回しにする
CTA_AFFILIATE = "ちなみに私が実際に使ってよかったのがこれ👇\n{name}\n{url}"


def pick_generic_seed(count):
    """カウント(0始まり)で汎用の問いかけを順番に選ぶ（末尾を超えたら先頭へ）"""
    return GENERIC_SEED_QUESTIONS[count % len(GENERIC_SEED_QUESTIONS)]


def cta_line_for_cycle(count, note_url="", affiliate=None):
    """投稿カウントから、1コメ目の末尾に付けるCTA行を返す。
    余り0=保存 / 余り1=フォロー / 余り2=note誘導 / 余り3=リポスト or アフィリエイト。
    note誘導の回でURLが無ければ保存CTAにフォールバックする。
    affiliate: {"name": 商品名, "url": リンク} を渡すと、リポスト枠が
      「リポスト⇄アフィリエイト」の交互ローテーションになる。
      Noneや空のとき（=楽天未登録の今）は従来通りリポストのみで、本番に影響しない。"""
    cycle = count % 4
    if cycle == 0:
        return CTA_SAVE
    if cycle == 1:
        return CTA_FOLLOW
    if cycle == 2:
        if note_url:
            return CTA_NOTE.format(url=note_url)
        return CTA_SAVE  # URLが無いときは保存CTAで代用（リンク無し事故を防ぐ）
    # cycle == 3: リポスト枠。アフィリ商品があれば交互に差し込む
    # cycle3が回ってきた回数（count//4）の偶奇で、リポストとアフィリを1回ずつ交互に出す
    if affiliate and affiliate.get("url") and affiliate.get("name"):
        if (count // 4) % 2 == 1:  # 奇数番目のcycle3回はアフィリにする
            return CTA_AFFILIATE.format(name=affiliate["name"], url=affiliate["url"])
    return CTA_REPOST


def build_seed_comment(base, cta="", deep_dive=False):
    """1コメ目の本文を作る。
    base: 深掘り本文（posts[1]）または汎用の問いかけ
    cta: 末尾に付けるCTA行（空文字なら付けない）
    deep_dive: Trueならリード行を先頭に付ける（本文との書き出し重複を避ける）"""
    text = base
    if deep_dive:
        text = f"{DEEP_DIVE_LEAD}\n\n{base}"  # リード行＋2行空けて本文
    if cta:
        text = f"{text}\n\n{cta}"  # 2行空けてCTAを足す
    return text[:MAX_LEN]  # 念のため500字に丸める
