import random  # ランダムな数を作るための道具を読み込む

# =============================================
# ⚔️  RPG風じゃんけんゲーム  ⚔️
# じゃんけんで敵を倒してレベルアップしよう！
# =============================================

# じゃんけんの手の一覧（リスト = 複数の値をまとめたもの）
HANDS = ["グー", "チョキ", "パー"]

# 敵の名前一覧（レベルが上がると強い敵が出てくる）
ENEMY_NAMES = ["スライム", "ゴブリン", "オーク", "トロール", "ドラゴン", "魔王"]

# 区切り線（見た目をきれいにするための文字）
LINE = "=" * 45
THIN_LINE = "-" * 45


# ------------------------------------------------
# レベルアップに必要な経験値を計算する関数
# 関数 = 何度でも使える「処理のまとまり」
# ------------------------------------------------
def get_exp_needed(level):
    # レベル × 10 の経験値が必要（レベルが高いほど多くEXPが必要）
    return level * 10


# ------------------------------------------------
# プレイヤー（自分）のデータを作る関数
# ------------------------------------------------
def create_player():
    # 辞書 = 名前と値のセットでデータをまとめたもの
    return {
        "name":    "勇者",   # プレイヤーの名前
        "level":   1,        # 最初はレベル1
        "exp":     0,        # 経験値はゼロからスタート
        "hp":      30,       # 現在のHP（0になるとゲームオーバー）
        "max_hp":  30,       # 最大HP（レベルアップで増える）
        "attack":  5,        # 攻撃力（レベルアップで増える）
        "kills":   0,        # 倒した敵の数
    }


# ------------------------------------------------
# 敵のデータを作る関数（プレイヤーのレベルに応じて強くなる）
# ------------------------------------------------
def create_enemy(player_level):
    # レベルに応じた敵の名前を選ぶ（リストの上限を超えないように min を使う）
    name_index = min(player_level - 1, len(ENEMY_NAMES) - 1)
    enemy_name = ENEMY_NAMES[name_index]

    # 敵のHPと攻撃力をレベルに応じて計算
    enemy_hp = 10 + player_level * 5       # HPはレベルが高いほど増える
    enemy_attack = 2 + player_level * 2    # 攻撃力もレベルが高いほど増える

    return {
        "name":    enemy_name,
        "level":   player_level,
        "hp":      enemy_hp,
        "max_hp":  enemy_hp,
        "attack":  enemy_attack,
    }


# ------------------------------------------------
# じゃんけんの勝ち負けを判定する関数
# 戻り値 = "win"（勝ち）/ "lose"（負け）/ "draw"（あいこ）
# ------------------------------------------------
def judge_janken(player_hand, enemy_hand):
    # 同じ手ならあいこ
    if player_hand == enemy_hand:
        return "draw"

    # 勝ちのパターンをすべて書き出す
    winning_patterns = [
        ("グー",   "チョキ"),   # グーはチョキに勝つ
        ("チョキ", "パー"),     # チョキはパーに勝つ
        ("パー",   "グー"),     # パーはグーに勝つ
    ]

    # プレイヤーの手が「勝ちのパターン」に含まれていれば勝ち
    if (player_hand, enemy_hand) in winning_patterns:
        return "win"

    # それ以外はすべて負け
    return "lose"


# ------------------------------------------------
# 現在の状態（ステータス）を画面に表示する関数
# ------------------------------------------------
def show_status(player, enemy):
    # プレイヤーのHPバー（記号で残りHPを見える化）
    player_hp_bar = make_hp_bar(player["hp"], player["max_hp"])
    enemy_hp_bar  = make_hp_bar(enemy["hp"],  enemy["max_hp"])

    print(f"\n{LINE}")
    print(f" ⚔️  【{player['name']}】  Lv.{player['level']}")
    print(f"    HP: {player_hp_bar} {player['hp']}/{player['max_hp']}")
    print(f"    EXP: {player['exp']}/{get_exp_needed(player['level'])}  攻撃力: {player['attack']}")
    print(THIN_LINE)
    print(f" 👾 【{enemy['name']}】  Lv.{enemy['level']}")
    print(f"    HP: {enemy_hp_bar} {enemy['hp']}/{enemy['max_hp']}")
    print(LINE)


# ------------------------------------------------
# HPバー（残りHPを記号で表す）を作る関数
# 例: ████░░░░  → HPが半分残っている状態
# ------------------------------------------------
def make_hp_bar(current_hp, max_hp):
    bar_length = 10                          # バーの長さ（記号の数）
    filled = int(current_hp / max_hp * bar_length)   # 残っているHP分の記号数
    empty  = bar_length - filled             # なくなったHP分の記号数

    # ████ がHP残量、░░░░ が失ったHP量
    return "█" * filled + "░" * empty


# ------------------------------------------------
# メインゲームの処理（ゲーム全体の流れを管理する）
# ------------------------------------------------
def main():
    # タイトル表示
    print(f"\n{LINE}")
    print("    ⚔️   RPG風じゃんけん   ⚔️")
    print("  じゃんけんで敵を倒してレベルアップ！")
    print(LINE)

    # プレイヤーと最初の敵を作る
    player = create_player()
    enemy  = create_enemy(player["level"])

    print(f"\n  最初の敵が現れた！")
    print(f"  👾 【{enemy['name']}】 Lv.{enemy['level']}  HP:{enemy['max_hp']}")

    # ゲームのメインループ（0を入力するまでずっと繰り返す）
    while True:
        # 現在のステータスを表示
        show_status(player, enemy)

        # プレイヤーに手を選んでもらう
        print("\n  手を選んでください：")
        print("    1: グー   2: チョキ   3: パー   0: やめる")
        choice = input("  番号を入力 >> ").strip()

        # 「0」でゲーム終了
        if choice == "0":
            print(f"\n  ゲームを終了します。お疲れ様でした！")
            print(f"  最終レベル: {player['level']}  倒した敵: {player['kills']}体")
            break

        # 「1」「2」「3」以外の入力はやり直し
        if choice not in ["1", "2", "3"]:
            print("  ⚠️  1〜3の番号を入力してください。")
            continue

        # 選んだ番号を手の名前に変換（"1" → "グー" など）
        player_hand = HANDS[int(choice) - 1]

        # 敵はランダムに手を選ぶ
        enemy_hand = random.choice(HANDS)

        # じゃんけんの結果を表示
        print(f"\n  あなた: {player_hand}  ✊  {enemy['name']}: {enemy_hand}")

        # 勝ち負けあいこを判定
        result = judge_janken(player_hand, enemy_hand)

        # ---- 勝った場合 ----
        if result == "win":
            damage = player["attack"]        # 与えるダメージ = プレイヤーの攻撃力
            enemy["hp"] -= damage            # 敵のHPを減らす
            print(f"  ✨ 勝ち！ {enemy['name']}に {damage} ダメージ！")

            # 敵のHPが0以下になったら倒した
            if enemy["hp"] <= 0:
                print(f"\n  🎉 {enemy['name']}を倒した！")
                player["kills"] += 1         # 倒した数を増やす

                # 獲得EXPを計算（敵が強いほどたくさん貰える）
                gained_exp = 5 + enemy["level"] * 3
                player["exp"] += gained_exp
                print(f"  ✨ 経験値 +{gained_exp}！  (合計: {player['exp']})")

                # レベルアップのチェック（必要EXPを超えたらレベルアップ）
                while player["exp"] >= get_exp_needed(player["level"]):
                    player["exp"]    -= get_exp_needed(player["level"])  # 超えた分を引く
                    player["level"]  += 1    # レベルを1上げる
                    player["max_hp"] += 10   # 最大HPを増やす
                    player["hp"]      = player["max_hp"]  # HPを全回復
                    player["attack"] += 2    # 攻撃力を増やす
                    print(f"\n  ★★★ レベルアップ！ → Lv.{player['level']} ★★★")
                    print(f"  HPが全回復！  最大HP +10  攻撃力 +2")

                # 次の敵を出現させる
                enemy = create_enemy(player["level"])
                print(f"\n  新たな敵が現れた！")
                print(f"  👾 【{enemy['name']}】 Lv.{enemy['level']}  HP:{enemy['max_hp']}")

        # ---- 負けた場合 ----
        elif result == "lose":
            damage = enemy["attack"]         # 受けるダメージ = 敵の攻撃力
            player["hp"] -= damage           # プレイヤーのHPを減らす
            print(f"  💥 負け！ {damage} ダメージを受けた！")

            # プレイヤーのHPが0以下になったらゲームオーバー
            if player["hp"] <= 0:
                player["hp"] = 0             # マイナス表示にならないよう0にする
                print(f"\n  💀 {enemy['name']}に倒されてしまった...")
                print(f"\n{LINE}")
                print(f"  ===  ゲームオーバー  ===")
                print(f"  最終レベル:  {player['level']}")
                print(f"  倒した敵:    {player['kills']} 体")
                print(LINE)
                break

        # ---- あいこの場合 ----
        else:
            print(f"  🤝 あいこ！  お互いにダメージなし。")


# ------------------------------------------------
# このファイルを直接実行したときだけ main() を呼ぶ
# （他のファイルから読み込まれたときは呼ばない）
# ------------------------------------------------
if __name__ == "__main__":
    main()
