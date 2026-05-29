// ────────── 振替フォーム ──────────
// 口座間の振替を入力するモーダル（背景タップで閉じる）
import { useState } from "react";
import { Transfer, Account } from "../types";
import { Input } from "./ui";
import {
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_BORDER,
  COLOR_BACKGROUND,
} from "../utils/styles";
import { parseYenAmount } from "../utils/format";

// このコンポーネントが受け取る props の型
interface TransferFormProps {
  accounts: Account[];
  onSubmit: (transfer: Transfer) => void;
  onCancel: () => void;
}

// セレクトボックスのスタイル（ui.tsx の Select と合わせた見た目）
const SELECT_STYLE: React.CSSProperties = {
  width: "100%",
  background: COLOR_BACKGROUND,
  border: `1px solid ${COLOR_BORDER}`,
  borderRadius: 10,
  color: COLOR_TEXT_PRIMARY,
  fontSize: 15,
  padding: "12px 14px",
  appearance: "none",
};

export default function TransferForm({ accounts, onSubmit, onCancel }: TransferFormProps) {
  // 今日の日付を初期値にする
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  // 送金元・送金先の口座ID（口座の先頭2件を初期値に）
  const [fromAccountId, setFromAccountId] = useState(accounts[0]?.id || "");
  const [toAccountId, setToAccountId] = useState(accounts[1]?.id || "");
  const [amount, setAmount] = useState("");
  const [memo, setMemo] = useState("");
  // バリデーションエラーメッセージ
  const [err, setErr] = useState("");

  // 振替ボタンを押した時の処理
  function handleSubmit() {
    if (!fromAccountId || !toAccountId) { setErr("口座を選んでください"); return; }
    // 同じ口座への振替はエラー
    if (fromAccountId === toAccountId) { setErr("同じ口座への振替はできません"); return; }
    const amountNum = parseYenAmount(amount);
    if (amountNum <= 0) { setErr("金額を入力してください"); return; }
    onSubmit({
      id: crypto.randomUUID(),
      date,
      fromAccountId,
      toAccountId,
      amount: amountNum,
      memo: memo || undefined,
    });
  }

  return (
    // 背景（半透明の黒）をタップすると閉じる
    <div
      onClick={onCancel}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.72)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      {/* カード本体はタップしても閉じない（stopPropagation） */}
      <div onClick={e => e.stopPropagation()} style={{ ...STYLE_CARD, width: "100%", maxWidth: 360 }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: COLOR_TEXT_PRIMARY, marginBottom: 16 }}>
          口座間の振替
        </div>

        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 4 }}>日付</div>
        <Input value={date} onChange={e => setDate(e.target.value)} type="date" />

        <div style={{ height: 10 }} />
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 4 }}>送金元</div>
        {/* 口座名を表示するため <select> を直接使う */}
        <select
          value={fromAccountId}
          onChange={e => setFromAccountId(e.target.value)}
          style={SELECT_STYLE}
        >
          {accounts.map(a => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>

        <div style={{ height: 10 }} />
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 4 }}>送金先</div>
        <select
          value={toAccountId}
          onChange={e => setToAccountId(e.target.value)}
          style={SELECT_STYLE}
        >
          {accounts.map(a => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>

        <div style={{ height: 10 }} />
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 4 }}>金額</div>
        <Input value={amount} onChange={e => setAmount(e.target.value)} money placeholder="0" />

        <div style={{ height: 10 }} />
        <div style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, marginBottom: 4 }}>メモ（任意）</div>
        <Input value={memo} onChange={e => setMemo(e.target.value)} placeholder="" />

        {/* エラーメッセージ */}
        {err && <div style={{ color: "#f87171", fontSize: 13, marginTop: 10 }}>{err}</div>}

        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <button type="button" onClick={onCancel} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1 }}>
            キャンセル
          </button>
          <button type="button" onClick={handleSubmit} style={{ ...STYLE_BUTTON_PRIMARY, flex: 1 }}>
            振替する
          </button>
        </div>
      </div>
    </div>
  );
}
