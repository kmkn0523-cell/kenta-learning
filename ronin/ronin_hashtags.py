# ronin_hashtags.py
# @RoninWords用：ハッシュタグを4セットで回す（発見タブ流入を広げる）
# 投稿カウントを渡すと A→B→C→D→A... の順でセットを返す純粋関数

# 4つのハッシュタグセット（1セット3個に抑える＝スパム判定回避）
HASHTAG_SETS = {
    "A": "#JapaneseWisdom #Bushido #Zen",            # 王道（コアの世界観）
    "B": "#StoicMindset #SelfDiscipline #Mindset",   # 越境（自己鍛錬・ストイック層へ）
    "C": "#Discipline #Resilience #Focus",           # 行動（モチベ層へ）
    "D": "#Samurai #Kanji #RoninWords",              # ブランド（指名検索を育てる）
}

# 回す順番（リストの順にローテーションする）
_ROTATION = ["A", "B", "C", "D"]


def pick_hashtag_set(count):
    """投稿カウント(0始まり)から、その回に使うハッシュタグ文字列を返す"""
    key = _ROTATION[count % len(_ROTATION)]  # 余りでA〜Dを選ぶ
    return HASHTAG_SETS[key]
