# note_dedup.py
# noteの重複投稿を防ぐための純粋関数を集めたモジュール。
# release_note.py（記事選択）と post_to_note.py（公開）の両方から呼び出し、
# 「今日すでに投稿済みか？」の判定ロジックを1か所に統一する（判定のズレ＝事故を防ぐ）。


def already_posted_today(history, today):
    """投稿履歴の中に「今日」の投稿が1件でもあれば True を返す。

    複数のGitHub Actions実行が古い progress.json を掴んでも、最新の履歴さえ読めれば
    二重投稿を弾けるようにするためのガード関数。

    引数:
      history: [{"date": "2026/06/08 09:01", "article": "article_07.md", ...}, ...] のリスト
      today:   "2026/06/08" のような日付文字列（時刻は含めない・前方一致で判定）

    旧実装は history[-1]（末尾の1件）しか見ていなかったため、古いチェックアウトで
    末尾が前日になっていると今日分を見逃して重複投稿が起きた。ここでは全件を走査する。
    """
    if not history:                          # 履歴が空なら、まだ投稿していない
        return False
    for entry in history:                    # 末尾だけでなく全件をチェックする
        date_value = entry.get("date", "")   # date キーが無くても落ちないようにする
        if date_value.startswith(today):     # 今日の日付で始まる投稿が1件でもあれば
            return True
    return False
