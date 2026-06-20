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


# テーマ別の問いかけ。投稿テーマ名にキーワードが当たれば、その話題に刺さる問いかけを使う。
# 「自分のことだ」と思わせて返信（＝会話シグナル）を誘発し、reachを伸ばす狙い。
# どのキーワードにも当たらなければ汎用（GENERIC_SEED_QUESTIONS）にフォールバックする。
THEME_SEED_QUESTIONS = {
    "腸活": {
        "keywords": ["腸", "発酵", "便秘", "食物繊維", "プロバイオ", "フローラ", "オリゴ"],
        "questions": [
            "腸活で最初に変えた習慣って、なんだった？",
            "発酵食品で続いてるものある？納豆？ヨーグルト？",
            "お腹の調子が良い日って、肌の調子も良くない？",
        ],
    },
    "睡眠": {
        "keywords": ["睡眠", "寝", "夜更かし", "体内時計", "眠"],
        "questions": [
            "何時に寝てる？早く寝た翌朝の肌、違いある？",
            "夜のスマホ、やめられた人いる？コツ知りたい。",
            "寝不足の翌日、肌に一番出るのってどこ？",
        ],
    },
    "砂糖": {
        "keywords": ["砂糖", "甘い", "糖", "スイーツ", "間食"],
        "questions": [
            "甘いもの、どのくらいの頻度で食べてる？",
            "砂糖を減らして肌が変わった人、いる？",
            "間食やめるなら、まず何から減らす？",
        ],
    },
    "スキンケア": {
        "keywords": ["洗顔", "スキンケア", "保湿", "化粧", "クレンジング", "セラミド", "バリア", "毛穴"],
        "questions": [
            "今のスキンケア、何ステップ？減らしてみたことある？",
            "洗顔って朝もする派？しない派？",
            "これ使って合わなかった、ってアイテムある？",
        ],
    },
    "食事": {
        "keywords": ["コーヒー", "カフェイン", "お茶", "外食", "油", "脂質", "添加物"],
        "questions": [
            "コーヒー何杯飲んでる？お茶に変えたことある？",
            "外食が続いた週って、肌どうなる？",
            "飲み物を変えただけで肌が変わった経験、ある？",
        ],
    },
    "運動": {
        "keywords": ["運動", "筋トレ", "ウォーキング", "有酸素", "代謝"],
        "questions": [
            "運動の習慣ある？肌の調子と関係ありそう？",
            "歩く習慣、続いてる人いる？",
        ],
    },
    "ストレス": {
        "keywords": ["ストレス", "メンタル", "自律神経", "更年期", "ホルモン", "生理", "pms"],
        "questions": [
            "ストレスが溜まると、肌のどこに出る？",
            "生理前の肌荒れ、対策してることある？",
        ],
    },
    "栄養素": {
        "keywords": ["亜鉛", "鉄分", "ビタミン", "タンパク質", "オメガ", "マグネシウム", "サプリ"],
        "questions": [
            "サプリ、何か飲んでる？続いてるものある？",
            "栄養で意識して摂ってるものある？",
        ],
    },
    "紫外線水分": {
        "keywords": ["紫外線", "日焼け", "uv", "水分", "乾燥"],
        "questions": [
            "日焼け止め、毎日塗ってる？室内でも？",
            "1日どのくらい水を飲んでる？",
        ],
    },
}


def pick_seed_question(count, theme=""):
    """テーマに合う問いかけがあればそれを、無ければ汎用をカウント順に返す。
    テーマ連動で「自分のことだ」と思わせ、返信（＝会話シグナル）を誘発する狙い。"""
    haystack = (theme or "").lower()
    for category in THEME_SEED_QUESTIONS.values():
        if any(keyword.lower() in haystack for keyword in category["keywords"]):
            questions = category["questions"]
            return questions[count % len(questions)]  # 当たったカテゴリ内でカウント順に回す
    return pick_generic_seed(count)  # どれにも当たらなければ従来の汎用問いかけ


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
