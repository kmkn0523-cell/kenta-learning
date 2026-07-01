# ronin_reply_hunter.py
# @RoninWords リプ巡回ツール：他アカウントへのリプを「探す → 書く → 記録」まで1コマンドで回す
# 使い方: python3 ronin/ronin_reply_hunter.py
# ※ このツールは Threads に自動投稿しません。最後の投稿は必ず手動コピペ（ネット失敗・トークン切れの心配なし）
# ※ memoryの「最強のreach手段＝他者への手動リプ」を半自動化する道具

import json  # JSONファイル（ターゲット一覧・履歴）を読み書きする道具
import random  # 下書き3案をランダムに選ぶための道具
import subprocess  # WSL2でWindows側ブラウザを開くための道具
import webbrowser  # まず普通にブラウザを開いてみるための標準ライブラリ
from datetime import date  # 今日の日付・曜日を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

# テンプレ集・テーマ分類は共通モジュールから読み込む。
# 直接実行（python3 ronin/ronin_reply_hunter.py）でも、pytest 経由でも動くように2通り試す
try:
    from ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES  # ronin/ が import パスにある時
    from ronin_theme_classifier import KEYWORD_MAP  # ronin/ が import パスにある時
except ImportError:
    from ronin.ronin_comment_templates import COMMENT_TEMPLATES, GENERIC_TEMPLATES  # リポジトリ直下から動かす時
    from ronin.ronin_theme_classifier import KEYWORD_MAP  # リポジトリ直下から動かす時

# -----------------------------------------------
# ファイルの場所（このスクリプトと同じ ronin/ フォルダにある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent  # このファイルがある ronin/ フォルダ
TARGETS_PATH = BASE_DIR / "ronin_account_targets.json"  # 巡回先アカウントの一覧（読むだけ）
HISTORY_PATH = BASE_DIR / "ronin_reply_history.json"  # アカウント別リプ履歴（読み書き・無ければ初回）
DAILY_LOG_PATH = BASE_DIR / "ronin_daily_log.md"  # 日次ログ（その日のリプ件数を追記）

# 曜日を日本語1文字で出すための表（月曜=0 … 日曜=6 に対応）
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]

# どのカテゴリーにも当てはまらなかった時に表示する名前（汎用テンプレ用）
GENERIC_CATEGORY_NAME = "汎用（どのカテゴリにも当てはまらない時）"


# =================================================
# ここから「純粋ロジック」関数（入力→出力がはっきり・テスト対象）
# =================================================

def suggest_drafts(post_text):
    """投稿の本文を渡すと、合いそうな下書きを3案と、判定したカテゴリ名を返す。

    キーワードが一番多く当たったカテゴリを選ぶ。同点なら番号の若い方（①→⑥）。
    どれにも当たらなければ汎用テンプレを出す（取りこぼしゼロ）。
    """
    text = post_text.lower()  # 大文字小文字をそろえて当たり判定をブレなくする
    best_key = None  # いまのところ一番当たっているカテゴリ番号
    best_hits = 0  # その当たり数

    # "1"〜"6" を必ず若い番号順に調べる（結果が毎回同じになるように順序を固定）
    for key in ["1", "2", "3", "4", "5", "6"]:
        # そのカテゴリのキーワードが本文に何個含まれるか数える
        hits = sum(1 for word in KEYWORD_MAP[key] if word.lower() in text)
        # 「今より多く当たった時だけ」更新 → 同点のときは先に見た若い番号が残る
        if hits > best_hits:
            best_hits = hits
            best_key = key

    # どのカテゴリーにも当たらなかった → 汎用テンプレから3案
    if best_key is None:
        drafts = random.sample(GENERIC_TEMPLATES, 3)
        return drafts, GENERIC_CATEGORY_NAME

    # 当たったカテゴリーのテンプレから3案をランダムに選ぶ
    category = COMMENT_TEMPLATES[best_key]
    drafts = random.sample(category["comments"], 3)
    return drafts, category["name"]


def sort_round_list(targets, history):
    """巡回順に並べ替えて返す。まだリプしてない人を最優先、あとは前回リプが古い順。

    同じ条件（みんな未リプ・前回日が同じ）のときは元の並びを保つ（安定ソート）。
    """
    def sort_key(target):
        # その人の履歴を取り出す（無ければ None）
        entry = history.get(target["handle"])
        # 履歴が無い／前回リプ日が空 = 未リプ → (0, "") で一番上にくる
        if not entry or not entry.get("last_replied_at"):
            return (0, "")
        # リプ済み → (1, 前回日) で、未リプの後ろに・日付が古い順に並ぶ
        return (1, entry["last_replied_at"])

    # sorted は安定ソートなので、同じキー同士は元の順番のまま保たれる
    return sorted(targets, key=sort_key)


def record_reply(history, handle, today):
    """リプ1件を履歴に足して、新しい履歴dictを返す（元の history は壊さない）。"""
    # 中身ごとコピーして新しい辞書を作る（元データを書き換えないため）
    new_history = {h: dict(value) for h, value in history.items()}

    if handle in new_history:
        # すでにいる人 → 件数を1増やして、前回リプ日を今日に更新
        new_history[handle]["total_replies"] += 1
        new_history[handle]["last_replied_at"] = today
    else:
        # 初めての人 → 件数1で新しく登録
        new_history[handle] = {"last_replied_at": today, "total_replies": 1}

    return new_history


def update_daily_log_text(existing_text, count, today_date):
    """日次ログの文字列に、その日のリプ件数を書き込んだ文字列を返す（ファイルは触らない）。

    今日の見出しが無ければ新しいブロックを末尾に追記。
    あれば、その下の「- リプ件数:」の行だけ差し替える（手動投稿数・気づきは残す）。
    """
    iso = today_date.isoformat()  # 例: "2026-06-07"
    weekday = WEEKDAY_JP[today_date.weekday()]  # 例: "日"
    heading = f"## {iso}（{weekday}）"  # 例: "## 2026-06-07（日）"
    reply_line = f"- リプ件数: {count}"  # 書き込む件数の行

    # --- 今日の見出しがもう有る場合：件数の行だけ差し替える ---
    if heading in existing_text:
        result_lines = []  # 作り直した行をためる箱
        in_today_block = False  # いま今日の見出しの中を読んでいるか
        already_replaced = False  # 件数行をもう差し替えたか（最初の1回だけ）

        for line in existing_text.split("\n"):
            # 見出し行に来たら、それが今日の見出しかどうかで「中にいる」を切り替える
            if line.startswith("## "):
                in_today_block = (line == heading)
            # 今日のブロックの中で、まだ差し替えてない「- リプ件数:」行なら新しい件数に置き換える
            if in_today_block and not already_replaced and line.startswith("- リプ件数:"):
                result_lines.append(reply_line)
                already_replaced = True
                continue  # 元の件数行は捨てる
            result_lines.append(line)  # それ以外の行はそのまま残す

        return "\n".join(result_lines)

    # --- 今日の見出しが無い場合：末尾に新しいブロックを追記する ---
    # 手動投稿数・気づきは空欄にしてKentaが夜に手書きできるようにする
    block = f"\n{heading}\n{reply_line}\n- 手動投稿数:\n- 気づき:\n"
    # 末尾の改行を一度そろえてから、改行＋ブロックをつなぐ（よけいな空行を増やさない）
    return existing_text.rstrip("\n") + "\n" + block


# =================================================
# ここから「ファイル・ブラウザ・対話」担当（テスト対象外）
# =================================================

def load_targets():
    """ronin_account_targets.json を読んで targets リストを返す。無い/壊れていたら None。"""
    try:
        with open(TARGETS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data["targets"]  # アカウントのリスト
    except FileNotFoundError:
        print(f"⚠ ターゲット一覧が見つかりません: {TARGETS_PATH}")
        return None
    except (json.JSONDecodeError, KeyError) as error:
        # JSONが壊れている／"targets"キーが無い → 巡回できないので None
        print(f"⚠ ターゲット一覧が読めません（壊れています）: {error}")
        return None


def load_history():
    """ronin_reply_history.json を読む。

    ファイルが無い → 初回とみなして空の履歴 {} を返す（正常）。
    ファイルが壊れている → None を返す（呼び出し側で終了。累計を勝手に上書きしないため）。
    """
    if not HISTORY_PATH.exists():
        return {}  # 初回は履歴ゼロでOK
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("history", {})  # 中の "history" 部分だけ取り出す
    except (json.JSONDecodeError, KeyError) as error:
        # 壊れている時は None。空で上書きするとリプ累計が消えてしまうので安全側に倒す
        print(f"⚠ 履歴ファイルが壊れています: {error}")
        return None


def save_history(history):
    """履歴を ronin_reply_history.json に書き込む（version と更新日も一緒に保存）。"""
    payload = {
        "version": "1.0",  # 形式のバージョン
        "updated_at": date.today().isoformat(),  # 最終更新日（ISO形式）
        "history": history,  # アカウント別の {前回リプ日・累計件数}
    }
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)  # 日本語をそのまま・読みやすく
        return True
    except OSError as error:
        print(f"⚠ 履歴の保存に失敗しました: {error}")
        return False


def open_account(url):
    """ブラウザでURLを開く（WSL2対応の段階フォールバック）。最低でもURLは必ず画面に出す。"""
    print(f"\n🔗 開くURL: {url}")  # 自動で開けなくてもコピーできるよう先に表示
    # ① まず普通のブラウザ起動を試す
    try:
        if webbrowser.open(url):
            return True
    except Exception:
        pass  # ダメでも次のやり方を試すので握りつぶす
    # ② WSL2向け：Windows側のブラウザで開く
    try:
        subprocess.run(
            ["cmd.exe", "/c", "start", "", url],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        pass
    # ③ どちらも無理 → 上に出したURLをKentaが手で開く
    print("（自動で開けませんでした。上のURLをコピーして開いてください）")
    return False


def append_daily_log(count, today):
    """ronin_daily_log.md にその日のリプ件数を書き込む（中身の計算は update_daily_log_text）。

    ファイルが無い/書けない時は警告だけ出してツールは続行する（件数は履歴側に残る）。
    """
    try:
        if DAILY_LOG_PATH.exists():
            with open(DAILY_LOG_PATH, encoding="utf-8") as f:
                existing = f.read()
        else:
            existing = "# ronin 日次ログ\n"  # 無ければ最低限の見出しから作る
        new_text = update_daily_log_text(existing, count, today)
        with open(DAILY_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(new_text)
        return True
    except OSError as error:
        print(f"⚠ 日次ログに書けませんでした（件数は履歴に残っています）: {error}")
        return False


def show_round_list(targets, history):
    """巡回リストを並べて画面に表示し、並べ替え済みのリストを返す。"""
    ordered = sort_round_list(targets, history)  # 未リプ最優先 → 古い順に並べる
    print("\n" + "=" * 60)
    print("  今日のリプ巡回リスト（上から順に回るのがおすすめ）")
    print("=" * 60)
    for i, target in enumerate(ordered, 1):
        handle = target["handle"]
        entry = history.get(handle)
        # 前回リプ日があれば「前回◯◯（累計N）」、無ければ「未リプ」と出す
        if entry and entry.get("last_replied_at"):
            status = f"前回 {entry['last_replied_at']}（累計{entry.get('total_replies', 0)}）"
        else:
            status = "未リプ"
        print(f"\n  [{i}] {handle}  {status}")
        if target.get("theme"):
            print(f"       テーマ: {target['theme']}")
        if target.get("notes"):
            print(f"       絡みどころ: {target['notes']}")
    print("\n" + "=" * 60)
    return ordered


def patrol_one_account(target, history):
    """1アカウント内で「投稿文を貼る → 下書き提示 → 記録」を繰り返す。

    更新後の history と、このアカウントで記録したリプ数を返す。
    """
    handle = target["handle"]
    added = 0  # このアカウントで記録したリプ数

    while True:
        print(f"\n--- {handle} を巡回中 ---")
        print("良い投稿を見つけたら本文を貼り付けてください（このアカウントを終わるなら空Enter）")
        post_text = input("投稿本文: ").strip()
        if not post_text:
            break  # 空Enter → このアカウントを終えて一覧へ戻る

        # 下書きを出す。気に入らなければ r で別の3案を出し直せる
        while True:
            drafts, category = suggest_drafts(post_text)
            print(f"\n【判定カテゴリ】{category}")
            print("下書き3案:")
            for i, draft in enumerate(drafts, 1):
                print(f"  [{i}] {draft}")
            print("  r: 別の3案を見る   s: この投稿はスキップ")
            choice = input("使う番号 / r / s: ").strip().lower()

            if choice == "s":
                break  # この投稿はやめて次の投稿へ
            if choice == "r":
                continue  # もう一度 suggest_drafts（別のランダム3案）
            if choice.isdigit() and 1 <= int(choice) <= len(drafts):
                chosen = drafts[int(choice) - 1]
                print("\n" + "=" * 60)
                print("✅ このリプをコピーしてThreadsアプリで投稿してください")
                print("=" * 60)
                print(chosen)
                print("=" * 60)
                input("投稿したらEnterを押す（記録します）")
                # 履歴を更新（record_reply は新しいdictを返すので入れ替える）
                history = record_reply(history, handle, date.today().isoformat())
                added += 1
                print(f"記録しました（このアカウント {added} 件目）")
                break  # 次の投稿へ
            print("⚠ 番号か r / s を入力してください")

    return history, added


def main():
    """対話ループ全体。巡回リスト表示 → アカウント選択 → リプ記録 → 終了時にログ追記。"""
    print("\n" + "=" * 60)
    print("  @RoninWords リプ巡回ツール（探す → 書く → 記録 を1コマンドで）")
    print("=" * 60)
    print("使い方:")
    print("  1. 巡回リストから1人選ぶ → Threadsが開く")
    print("  2. 良い投稿を見つけたら本文を貼り付ける → 英語の下書き3案が出る")
    print("  3. 1案を選んでコピー → Threadsアプリで自分で投稿")
    print("  4. 投稿したら記録 → 件数が貯まる")
    print("  ※ 投稿はすべて手動コピペ（このツールはThreadsに自動投稿しません）")

    # ① ターゲット読み込み（無い/壊れていたら巡回できないので終了）
    targets = load_targets()
    if not targets:
        print("巡回できないので終了します。")
        return

    # ② 履歴読み込み（無ければ空＝初回／壊れていたら終了して中身確認を促す）
    history = load_history()
    if history is None:
        print("履歴ファイルが壊れています。累計を消さないため、中身を確認してから再実行してください。")
        return

    reply_count = 0  # 今日のリプ件数（全アカウント合計）

    while True:
        ordered = show_round_list(targets, history)
        print("\n操作を選んでください：")
        print(f"  番号（1〜{len(ordered)}）: そのアカウントを開いて巡回")
        print("  s: 今日のリプ件数を記録して終了")
        choice = input("入力: ").strip().lower()

        if choice == "s":
            break  # 終了処理へ
        if not choice.isdigit():
            print("⚠ 番号か s を入力してください")
            continue
        index = int(choice) - 1
        if not (0 <= index < len(ordered)):
            print("⚠ リストにない番号です")
            continue

        # 選んだアカウントをブラウザで開いて、その中で巡回する
        target = ordered[index]
        open_account(target["url"])
        history, added = patrol_one_account(target, history)
        reply_count += added

    # ③ 終了処理：履歴を保存 → 日次ログに件数を追記
    today = date.today()
    save_history(history)
    append_daily_log(reply_count, today)
    print(f"\nお疲れ様でした！今日のリプ件数: {reply_count}")
    print("（手動投稿数・気づきは夜に ronin_daily_log.md へ手書きで追記してください）")


if __name__ == "__main__":
    main()
