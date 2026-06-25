# ronin_reel_engine.py
# @RoninWords Instagram Reels 自動生成・自動投稿エンジン（GitHub Actions専用・全自動）
# 格言1件を段階リビールする縦型動画を ffmpeg で作り、Reelsとして自動投稿する。
# generate（動画生成）と publish（公開）の2サブコマンドを持つ。

import json     # 設定・状態ファイルを読み書きする道具
import os       # 環境変数（トークン・有効化スイッチ）を読む道具
import subprocess  # ffmpeg を実行する道具
import sys      # コマンド引数（generate / publish）を読む道具
import time     # URL配信待ち・ポーリングに使う道具
from datetime import datetime, timezone, timedelta  # 日本時間で「今日」を求める道具
from pathlib import Path  # ファイルの場所を組み立てる道具

import requests  # 動画URLの配信確認・API投稿に使う道具


# 投稿の末尾に付けるフォロー誘導文（既存の画像投稿と統一）
CTA = "Follow for one Japanese wisdom, every day."


def next_proverb_index(progress, total):
    """進捗から次に使う格言のインデックス（0始まり）を返す。末尾の次は先頭へ循環。"""
    current = progress.get("reel_index", -1)  # まだ無ければ -1 → 次は 0
    return (current + 1) % total


def frame_reveal_plan():
    """4フレームの『累積リビール』表示プランを返す。背景→日本語→ローマ字→英語の順。"""
    return [
        {"jp": False, "roma": False, "en": False},  # 1枚目: 和紙背景＋シールだけ
        {"jp": True,  "roma": False, "en": False},  # 2枚目: 日本語格言を出す
        {"jp": True,  "roma": True,  "en": False},  # 3枚目: ローマ字を足す
        {"jp": True,  "roma": True,  "en": True},   # 4枚目: 英語の意味＋CTA
    ]


def build_caption(proverb, hashtags):
    """格言の jp/roma/en と CTA・ハッシュタグから Reels キャプションを組み立てる。"""
    return (
        f"{proverb['jp']}\n{proverb['roma']}\n\n"
        f"{proverb['en']}\n\n"
        f"{CTA}\n\n{hashtags}"
    )


def build_raw_video_url(raw_video_base, filename):
    """動画の raw 公開URLを組み立てる。"""
    return f"{raw_video_base}/{filename}"


def build_ffmpeg_command(image_paths, audio_path, output_path, seconds_per_frame, fps, width, height, fade_duration):
    """静止画フレーム＋音源から縦型(9:16)H.264動画を作る ffmpeg コマンド（引数リスト）を返す。
    各フレームを seconds_per_frame 秒ずつ表示し、fadeで柔らかく出して concat で連結する。
    音声は動画の長さに合わせて -shortest で切る。"""
    command = ["ffmpeg", "-y"]  # -y: 既存ファイルを上書き
    for path in image_paths:  # フレームを1枚ずつ静止画入力として追加
        command += ["-loop", "1", "-t", str(seconds_per_frame), "-i", path]
    command += ["-i", audio_path]  # 最後に音源を追加（入力番号 = フレーム枚数）

    # 各フレームを縦型キャンバスに収め、fade-inで柔らかく出す filter を組み立てる
    filters = []
    for index in range(len(image_paths)):
        # 縦型(9:16)キャンバスに収める基本の変換（拡大縮小＋余白＋アスペクト比固定）
        base = (
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        )
        if index == 0:
            # 1枚目は黒フェードを掛けない（冒頭とサムネが真っ黒になるのを防ぐ・和紙背景で始める）
            filters.append(f"{base}[v{index}]")
        else:
            # 2枚目以降だけ黒からふわっと出してリビール感を出す
            filters.append(f"{base},fade=t=in:st=0:d={fade_duration}[v{index}]")
    concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
    filters.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[outv]")
    filter_complex = ";".join(filters)

    audio_index = len(image_paths)  # 音源の入力番号
    command += [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{audio_index}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    return command


def load_json(path, default):
    """JSONファイルを読み込む。無ければ default を返す。"""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """JSONファイルを書き出す（日本語そのまま・読みやすいインデント）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------------------------
# ファイルの場所・定数（このスクリプトと同じ ronin/ にある前提）
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "ronin_reel_engine_config.json"
AUDIO_PATH = BASE_DIR / "ronin_reel_assets" / "bgm.mp3"
FRAMES_TMP_DIR = BASE_DIR / "ronin_reel_frames_tmp"   # フレームPNGの一時置き場
REELS_DIR = BASE_DIR / "ronin_instagram_reels"
PENDING_PATH = BASE_DIR / "ronin_reel_pending.json"
PROGRESS_PATH = BASE_DIR / "ronin_reel_progress.json"
JST = timezone(timedelta(hours=9))  # 日本時間


def generate():
    """格言を選んで動画を生成し、pending.json に公開情報を書き出す。"""
    if os.environ.get("RONIN_REEL_ENGINE_ENABLED") != "true":
        print("RONIN_REEL_ENGINE_ENABLED が true でないため停止します。")
        return
    if not AUDIO_PATH.exists():  # 音源が無ければ著作権事故防止のため明確に停止
        print(f"音源が見つかりません: {AUDIO_PATH}（CC0音源を置いてください）")
        return

    config = load_json(str(CONFIG_PATH), default={})

    # 格言データとハッシュタグは既存スクリプトから読む（遅延importで副作用を避ける）
    sys.path.insert(0, str(BASE_DIR))  # ronin/ をimportパスに入れる
    from generate_ronin_cards import proverbs
    from ronin_hashtags import pick_hashtag_set

    total = min(config["total_proverbs"], len(proverbs))
    progress = load_json(str(PROGRESS_PATH), default={"reel_index": -1, "history": []})
    index = next_proverb_index(progress, total)
    proverb = proverbs[index]

    # フレームを描く（遅延import：Pillow依存をgenerate時だけに閉じ込める）
    from ronin_reel_frames import render_reveal_frames
    image_paths = render_reveal_frames(
        proverb, frame_reveal_plan(), str(FRAMES_TMP_DIR), config["width"], config["height"]
    )

    REELS_DIR.mkdir(exist_ok=True)  # 出力先フォルダを用意
    output_path = str(REELS_DIR / config["video_filename"])
    command = build_ffmpeg_command(
        image_paths, str(AUDIO_PATH), output_path,
        config["seconds_per_frame"], config["fps"], config["width"], config["height"],
        config["fade_duration"],
    )
    print("ffmpeg実行:", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:  # 生成失敗なら中身を出して停止
        print("ffmpeg失敗:", result.stderr[-1500:])
        return

    caption = build_caption(proverb, pick_hashtag_set(index))
    save_json(str(PENDING_PATH), {
        "proverb_index": index,
        "caption": caption,
        "video_filename": config["video_filename"],
    })
    print(f"生成完了: index={index}, jp={proverb['jp']} → {output_path}")


def wait_for_url(url, max_wait=180):
    """動画の raw URL が配信され始める（HTTP 200）まで待つ。"""
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return True
        except Exception as error:
            print(f"URL確認エラー: {error}")
        time.sleep(15)
        waited += 15
    return False


def cover_thumb_offset_ms(config):
    """カバー（サムネ）に使う動画内の時刻をミリ秒で返す。
    最後のフレーム（格言＋ローマ字＋英語が全部出た状態）の中央あたりを指す。
    黒フェードの後で確実に内容が見える瞬間なので、真っ黒サムネを防げる。"""
    frame_count = len(frame_reveal_plan())                 # フレーム枚数（=4）
    seconds_per_frame = config["seconds_per_frame"]         # 1フレームの表示秒数
    # 最終フレームの開始時刻＋半分 = 全要素が出そろった真ん中
    seconds = (frame_count - 1) * seconds_per_frame + seconds_per_frame / 2
    return int(seconds * 1000)


def create_reels_container(video_url, caption, user_id, token, thumb_offset_ms=None):
    """media_type=REELS でコンテナ（下書き）を作り、creation_id を返す。
    thumb_offset_ms を渡すと、その時刻のフレームをカバー（サムネ）に使う。"""
    url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": token,
    }
    if thumb_offset_ms is not None:  # カバー位置の指定があれば追加（真っ黒サムネ対策）
        params["thumb_offset"] = thumb_offset_ms
    response = requests.post(url, params=params, timeout=60)
    data = response.json()
    if "id" in data:
        return data["id"]
    print(f"Reelsコンテナ作成失敗: {data}")
    return ""


def wait_for_container_ready(creation_id, token, max_wait=180):
    """動画コンテナの処理が FINISHED になるまで待つ（最大 max_wait 秒）。"""
    url = f"https://graph.facebook.com/v19.0/{creation_id}"
    params = {"fields": "status_code", "access_token": token}
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(url, params=params, timeout=15)
            status = response.json().get("status_code", "UNKNOWN")
            print(f"  コンテナ状態: {status}（{waited}秒経過）")
            if status == "FINISHED":
                # FINISHED直後でも内部処理が残ることがあるので30秒待つ（9007対策）
                time.sleep(30)
                return True
            if status == "ERROR":
                print(f"コンテナ処理エラー: {response.json()}")
                return False
        except Exception as error:
            print(f"状態確認エラー: {error}")
        time.sleep(10)
        waited += 10
    print(f"{max_wait}秒待っても処理が完了しませんでした。")
    return False


def publish():
    """pending.json を読み、動画URLの配信を待ってから Reels を公開する。"""
    if os.environ.get("RONIN_REEL_ENGINE_ENABLED") != "true":
        print("RONIN_REEL_ENGINE_ENABLED が true でないため停止します。")
        return

    config = load_json(str(CONFIG_PATH), default={})
    pending = load_json(str(PENDING_PATH), default={})
    if not pending:
        print("公開対象（pending.json）がありません。")
        return

    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]
    video_url = build_raw_video_url(config["raw_video_base"], pending["video_filename"])

    if not wait_for_url(video_url):  # URLが生えるまで待つ
        print(f"動画URLが配信されませんでした: {video_url}")
        return

    thumb_offset_ms = cover_thumb_offset_ms(config)  # 全要素が出た最終フレームをカバーに
    creation_id = create_reels_container(
        video_url, pending["caption"], user_id, token, thumb_offset_ms
    )
    if not creation_id:
        return
    if not wait_for_container_ready(creation_id, token):
        print("動画の処理が完了しませんでした。")
        return

    # 公開は既存スクリプトを再利用（env必須なので遅延import）
    sys.path.insert(0, str(BASE_DIR))
    from ronin_instagram_auto_post import publish_media
    result = publish_media(creation_id)
    if not result.get("id"):
        print(f"公開失敗: {result}")
        return

    # 進捗を進める・履歴に当日を追記
    progress = load_json(str(PROGRESS_PATH), default={"reel_index": -1, "history": []})
    today = datetime.now(JST).strftime("%Y-%m-%d")
    progress["reel_index"] = pending["proverb_index"]
    progress.setdefault("history", []).append(today)
    save_json(str(PROGRESS_PATH), progress)
    print(f"公開完了: post_id={result['id']}")


def main():
    """引数 generate / publish でサブコマンドを振り分ける。"""
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "generate":
        generate()
    elif command == "publish":
        publish()
    else:
        print("使い方: python ronin_reel_engine.py [generate|publish]")


if __name__ == "__main__":
    main()
