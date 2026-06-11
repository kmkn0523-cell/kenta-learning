// ────────── 「友達に教える」シェアカード ──────────
// 設定タブに置く、アプリ自体を広めてもらうためのカード
// スマホ: ネイティブのシェアシート（navigator.share）
// PC等: クリップボードにURLをコピーしてボタンの文言でフィードバック

import { useState } from "react";
import { STYLE_CARD, STYLE_BUTTON_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_NEGATIVE } from "../utils/styles";

// シェアで送る内容（OGP・index.html の説明文とトーンを合わせる）
const SHARE_TITLE = "BYB — Before You Broke";
const SHARE_TEXT = "収支を入力するだけ。グラフで家計が一目でわかる無料の家計簿アプリ";
export const SHARE_URL = "https://financeweb-nine.vercel.app";

export default function ShareCard() {
  // ボタンのフィードバック状態（"" = 通常 / copied = コピー成功 / error = 失敗）
  const [feedback, setFeedback] = useState<"" | "copied" | "error">("");

  async function share() {
    // スマホなどシェアシートが使える環境
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: SHARE_TITLE, text: SHARE_TEXT, url: SHARE_URL });
      } catch (_) {
        // ユーザーがシェアをキャンセルした場合もここに来る（正常系なので何もしない）
      }
      return;
    }
    // PC等：クリップボードにコピーする
    try {
      await navigator.clipboard.writeText(`${SHARE_TEXT} ${SHARE_URL}`);
      setFeedback("copied");
    } catch (_) {
      setFeedback("error");
    }
    // 2秒後にボタンを元の表示に戻す
    setTimeout(() => setFeedback(""), 2000);
  }

  return (
    <div style={{ ...STYLE_CARD, marginTop: 16 }}>
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 10 }}>
        友達に教える
      </div>
      <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, lineHeight: 1.7, marginBottom: 12 }}>
        BYBが役に立ったら、家族や友達にもシェアしてもらえると嬉しいです。
      </div>
      <button type="button" onClick={share} style={{ ...STYLE_BUTTON_PRIMARY, width: "100%" }}>
        {feedback === "copied" ? "✓ リンクをコピーしました" : "📣 友達に教える"}
      </button>
      {/* コピー失敗時だけ表示するエラーメッセージ（URLを直接見せて手動コピーできるように） */}
      {feedback === "error" && (
        <div style={{ fontSize: 12, color: COLOR_NEGATIVE, marginTop: 8, textAlign: "center", lineHeight: 1.6 }}>
          コピーできませんでした。このURLを直接共有してください：<br />
          {SHARE_URL}
        </div>
      )}
    </div>
  );
}
