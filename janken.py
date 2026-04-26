import random

HANDS = {
    1: ("グー",    "✊"),
    2: ("チョキ",  "✌️"),
    3: ("パー",    "✋"),
    4: ("ピストル","🤙"),
    5: ("忍者",    "🥷"),
}

# 各手が勝てる相手と、その理由
WIN_RULE: dict[int, dict[int, str]] = {
    1: {2: "グーがチョキを砕く",    4: "グーがピストルを弾く"},
    2: {3: "チョキがパーを切る",    5: "チョキが忍者の衣を裂く"},
    3: {1: "パーがグーを包む",      4: "パーがピストルを詰まらせる"},
    4: {2: "ピストルがチョキを吹き飛ばす", 5: "ピストルが忍者を射抜く"},
    5: {1: "忍者がグーをかわす",    3: "忍者がパーを切り裂く"},
}


def get_result(player: int, cpu: int) -> tuple[str, str]:
    """勝敗を判定して (結果, 理由) を返す"""
    if player == cpu:
        return "draw", ""
    elif cpu in WIN_RULE[player]:
        return "win", WIN_RULE[player][cpu]
    else:
        return "lose", WIN_RULE[cpu][player]


def show_result(player: int, cpu: int, result: str, reason: str) -> None:
    p_name, p_emoji = HANDS[player]
    c_name, c_emoji = HANDS[cpu]
    print(f"  あなた: {p_name} {p_emoji}  vs  CPU: {c_name} {c_emoji}")
    if result == "win":
        print(f"  → {reason}")
        print("  → あなたの勝ち! 🎉")
    elif result == "lose":
        print(f"  → {reason}")
        print("  → あなたの負け... 😢")
    else:
        print("  → 引き分け! 🤝")


def show_stats(wins: int, losses: int, draws: int) -> None:
    total = wins + losses + draws
    win_rate = (wins / total * 100) if total > 0 else 0
    print("\n========== 通算成績 ==========")
    print(f"  {wins}勝 {losses}敗 {draws}引き分け")
    print(f"  勝率: {win_rate:.1f}%")
    print("================================\n")


def main() -> None:
    print("===== 5本指じゃんけんゲーム =====\n")
    print("  グー < チョキ < パー < グー")
    print("  ピストル: グー・パーに負け、チョキ・忍者に勝つ")
    print("  忍者:     チョキ・ピストルに負け、グー・パーに勝つ\n")

    wins = 0
    losses = 0
    draws = 0

    choices = "  ".join(f"{k}:{v[0]}{v[1]}" for k, v in HANDS.items())

    while True:
        while True:
            print(f"手を選んでください: {choices}")
            choice = input("入力 (1〜5): ").strip()
            if choice in ("1", "2", "3", "4", "5"):
                player_hand = int(choice)
                break
            else:
                print("  ※ 1〜5のいずれかを入力してください。\n")

        cpu_hand = random.randint(1, 5)

        print()
        result, reason = get_result(player_hand, cpu_hand)
        show_result(player_hand, cpu_hand, result, reason)

        if result == "win":
            wins += 1
        elif result == "lose":
            losses += 1
        else:
            draws += 1

        print()
        again = input("もう一度やる? (y/n): ").strip().lower()
        print()

        if again != "y":
            break

    show_stats(wins, losses, draws)
    print("またね! 👋")


if __name__ == "__main__":
    main()
