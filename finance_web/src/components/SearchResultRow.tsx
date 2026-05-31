// ────────── 横断検索の結果1件を表示する行コンポーネント（読み取り専用） ──────────
// 検索結果（SearchResultItem）を1行だけ受け取って、見やすく並べて表示する
import { SearchResultItem } from "../utils/searchFilter";
import { formatYen } from "../utils/format";
import {
  COLOR_POSITIVE,    // 収入を表す緑
  COLOR_NEGATIVE,    // 支出を表す赤
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
} from "../utils/styles";

// このコンポーネントが受け取る値の形
interface SearchResultRowProps {
  item: SearchResultItem;          // 表示する結果1件
  accountName?: string;            // 口座名（引けなければ表示しない）
}

// 検索結果1件を1行で表示する
export default function SearchResultRow({ item, accountName }: SearchResultRowProps) {
  // 収入なら緑、支出なら赤に色分けする
  const isIncome = item.kind === "income";
  const accentColor = isIncome ? COLOR_POSITIVE : COLOR_NEGATIVE;
  // 金額の前に付ける符号（収入は「＋」、支出は「−」）
  const sign = isIncome ? "＋" : "−";

  return (
    <div
      style={{
        display: "flex",                    // 横並びにする
        alignItems: "center",               // 縦方向は中央ぞろえ
        gap: 12,                            // 要素どうしの間隔
        padding: "12px 14px",               // 内側の余白
        borderBottom: `1px solid ${COLOR_BORDER}`, // 行の下に薄い区切り線
      }}
    >
      {/* 左：収入/支出を表す丸いバッジ */}
      <div
        style={{
          flexShrink: 0,                    // 縮ませない
          width: 8,
          height: 8,
          borderRadius: "50%",              // まん丸にする
          background: accentColor,          // 収入=緑 / 支出=赤
        }}
      />

      {/* 中央：カテゴリ・メモ・日付・口座 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* 1段目：カテゴリ名（太字） */}
        <div
          style={{
            color: COLOR_TEXT_PRIMARY,
            fontSize: 14,
            fontWeight: 600,
            whiteSpace: "nowrap",           // 折り返さない
            overflow: "hidden",             // はみ出しは隠す
            textOverflow: "ellipsis",       // はみ出しは「…」にする
          }}
        >
          {item.category || "（カテゴリなし）"}
        </div>
        {/* 2段目：日付＋口座名＋メモ（薄い色の補足情報） */}
        <div
          style={{
            color: COLOR_TEXT_HINT,
            fontSize: 12,
            marginTop: 2,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {item.date}
          {accountName ? ` ・ ${accountName}` : ""}
          {item.memo ? ` ・ ${item.memo}` : ""}
        </div>
      </div>

      {/* 右：金額（収入=緑＋ / 支出=赤−） */}
      <div
        style={{
          flexShrink: 0,
          color: accentColor,
          fontSize: 15,
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums", // 数字の幅をそろえて見やすくする
        }}
      >
        {sign}
        {formatYen(item.amount)}
      </div>
    </div>
  );
}
