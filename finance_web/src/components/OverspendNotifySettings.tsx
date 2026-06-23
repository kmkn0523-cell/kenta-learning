// ────────── 使いすぎ通知 設定UI（共通部品） ──────────
// 予算セクションと設定タブの両方に置く。
//  ・オン/オフスイッチ
//  ・未許可なら「通知を許可」ボタン
//  ・許可状態の表示（拒否・非対応の案内）
import { CSSProperties } from "react";
import {
  STYLE_CARD,
  STYLE_BUTTON_OUTLINE,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "../utils/styles";

const STYLE_ROW: CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 };

interface OverspendNotifySettingsProps {
  enabled: boolean;                                    // オン/オフ
  onToggle: (value: boolean) => void;                 // スイッチ変更
  permission: NotificationPermission | "unsupported"; // 通知許可状態
  onRequestPermission: () => void;                    // 「通知を許可」ボタン
}

export default function OverspendNotifySettings(props: OverspendNotifySettingsProps) {
  const { enabled, onToggle, permission, onRequestPermission } = props;
  // 通知が実際に届く状態か（オン かつ 許可済み）
  const active = enabled && permission === "granted";

  return (
    <section style={{ ...STYLE_CARD, marginTop: 16 }}>
      <h3 style={{ fontSize: 15, color: COLOR_TEXT_PRIMARY, margin: "0 0 4px" }}>🔔 使いすぎ通知</h3>
      <p style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, margin: "0 0 14px" }}>
        カテゴリの支出が予算の80%・100%を超えたらお知らせします（このアプリを開いている時／開いた時）。
      </p>

      {/* オン/オフ */}
      <label style={{ ...STYLE_ROW, marginBottom: 12, cursor: "pointer" }}>
        <span style={{ fontSize: 13, color: COLOR_TEXT_PRIMARY }}>使いすぎ通知を受け取る</span>
        <input type="checkbox" checked={enabled} onChange={e => onToggle(e.target.checked)} />
      </label>

      {/* 許可の導線・状態表示 */}
      {permission === "unsupported" ? (
        <p style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, margin: 0 }}>
          お使いのブラウザは通知に対応していません。
        </p>
      ) : permission === "denied" ? (
        <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: 0 }}>
          通知がブロックされています。ブラウザの設定から許可してください。
        </p>
      ) : permission === "granted" ? (
        <p style={{ fontSize: 12, color: active ? COLOR_POSITIVE : COLOR_TEXT_SECONDARY, margin: 0 }}>
          {active ? "通知は有効です。" : "通知は許可済みです（スイッチをオンにしてください）。"}
        </p>
      ) : (
        <button type="button" style={{ ...STYLE_BUTTON_OUTLINE, width: "100%" }} onClick={onRequestPermission}>
          通知を許可する
        </button>
      )}
    </section>
  );
}
