# skin_note_matcher.py
# 投稿テーマ・本文に「いちばん内容が近い」無料note記事を選ぶ道具（計算だけの純粋関数）。
# CTAのnote誘導をテーマ連動にして、読者が「今読んだ話の続き」を押したくなる状態を作る。
# どれにも当てはまらなければ空文字を返す（呼び出し側が従来のローテに切り替える）。

# note記事URL → その記事を出す「目印キーワード」一覧。
# 目印は投稿テーマ名や本文によく出てくる言葉。"肌"や"ニキビ"のような全投稿共通の言葉は
# 入れない（どの記事にも当たってしまい区別できないため）。固有の言葉だけを選ぶ。
NOTE_KEYWORDS = {
    # 夜遅い食事と肌
    "https://note.com/neima/n/n919a2bcadbe6": ["夜遅く", "夜食", "夜食べ", "食べる時間", "寝る前", "夕食"],
    # 背中ニキビ・シャンプー
    "https://note.com/neima/n/n2f1b6631ec38": ["背中", "シャンプー", "頭皮"],
    # コーヒー・カフェイン
    "https://note.com/neima/n/n19fa579db70e": ["コーヒー", "カフェイン"],
    # リーキーガット（腸活してるのに治らない）
    "https://note.com/neima/n/n8d4de0dad736": ["リーキーガット", "腸漏れ", "腸もれ"],
    # 血糖値スパイク・抗糖化
    "https://note.com/neima/n/n5bd03ee8e761": ["血糖値", "血糖", "スパイク", "抗糖化", "糖化"],
    # 油・脂質・オメガ3
    "https://note.com/neima/n/n376b2cba9d4f": ["油", "脂質", "オメガ", "あぶら"],
    # ビタミンD（B/Cと区別するため固有名のみ）
    "https://note.com/neima/n/n59efb37557b5": ["ビタミンd"],
    # ヨーグルト・菌・発酵・フローラ
    "https://note.com/neima/n/n4f666fad60a9": ["ヨーグルト", "プロバイオティクス", "フローラ", "発酵", "乳酸菌", "オリゴ糖"],
    # 日焼け・紫外線
    "https://note.com/neima/n/n4b4e5b4804fc": ["日焼け", "紫外線", "uv"],
    # 水・水分（白湯=腸活noteと区別するためフレーズで）
    "https://note.com/neima/n/ndf95ee58b795": ["水分", "水を飲", "水の飲", "水道水", "脱水"],
    # 運動
    "https://note.com/neima/n/n8dd0a6de39e3": ["運動", "ウォーキング", "有酸素", "筋トレ"],
    # 乳製品（ヨーグルトは8に譲る）
    "https://note.com/neima/n/nd6c4a831644b": ["乳製品", "牛乳", "チーズ"],
    # 砂糖・甘いもの
    "https://note.com/neima/n/n4d52787c48d6": ["砂糖", "甘いもの", "甘い", "糖質"],
    # 亜鉛
    "https://note.com/neima/n/n5f339b9fb059": ["亜鉛"],
    # 睡眠
    "https://note.com/neima/n/n668abed2d2a7": ["睡眠", "寝", "夜更かし", "体内時計", "眠"],
    # ファスティング・断食
    "https://note.com/neima/n/ndc6a2082eae1": ["ファスティング", "断食", "16時間", "プチ断食", "空腹"],
    # 肌を荒らす食べ物・添加物・外食
    "https://note.com/neima/n/nb434b1f1f51d": ["添加物", "加工食品", "外食", "コンビニ"],
    # 洗顔・保湿・スキンケア
    "https://note.com/neima/n/n901a917a0d96": ["洗顔", "保湿", "スキンケア", "化粧落とし", "クレンジング", "洗いすぎ", "セラミド", "バリア機能"],
    # 腸活の基本（腸から治す3ステップ）
    "https://note.com/neima/n/n688396a1a5b9": ["腸活", "腸内", "腸と", "腸を", "腸の", "便秘", "食物繊維", "白湯", "セロトニン"],
}


def match_note_url(theme, text, articles):
    """投稿テーマ名＋本文に、いちばん目印キーワードが多く当たるnote記事のURLを返す。
    - theme: 投稿テーマ名（例「砂糖とニキビ」）
    - text : 投稿本文（テーマ名だけでは弱いとき本文からも拾う）
    - articles: note_promo_articles.json の articles（実在する記事だけを候補にする）
    1つも当たらなければ空文字を返す（呼び出し側で従来のローテに切り替える）。"""
    haystack = (theme or "").lower() + " " + (text or "").lower()  # 探す対象（小文字化でUV等を吸収）
    valid_urls = {a.get("url") for a in (articles or [])}  # 実際に宣伝対象になっている記事URLの集合
    best_url = ""    # 今のところ一番合っている記事URL
    best_score = 0   # その当たり数
    for url, keywords in NOTE_KEYWORDS.items():
        if url not in valid_urls:  # 記事一覧から消えた・差し替わったURLは出さない（壊れ防止）
            continue
        score = sum(1 for keyword in keywords if keyword.lower() in haystack)  # 当たった目印の数
        if score > best_score:  # より多く当たった記事を採用（同点は先に定義した方が残る）
            best_url = url
            best_score = score
    return best_url
