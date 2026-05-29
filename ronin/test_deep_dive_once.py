#!/usr/bin/env python3
# test_deep_dive_once.py
# Day29のdeep-diveスレッドを1件テスト投稿する（実行後に削除する）

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ronin_threads_action import post_deep_dive_thread

CARD_POST_ID = "17950014174175376"
DAY = 29

print(f"Day{DAY} のdeep-diveスレッドをテスト投稿します...")
post_deep_dive_thread(CARD_POST_ID, DAY)
print("完了。")
