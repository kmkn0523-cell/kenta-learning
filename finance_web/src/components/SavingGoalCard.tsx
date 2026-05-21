// ────────── 目標貯金カード ──────────
// 「2026年末までに100万円」のような貯金目標を1つ設定し、達成率・残り金額・月次必要額を表示する
// 現在の貯金額は口座残高の合計を使う（calculateAccountBalance）
// 目標未設定なら CTA ボタンを、設定済みなら進捗カードを表示する

import { useState } from "react";
import { SavingGoal, Account, Tx, Income, Transfer } from "../types";
import { parseYenAmount, formatYen } from "../utils/format";
import { newId } from "../utils/crypto";
import { calculateAccountBalance } from "../utils/accountBalance";
import {
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_TEXT_HINT,
  COLOR_BORDER,
  COLOR_ACCENT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
} from "../utils/styles";
import { Input } from "./ui";

interface SavingGoalCardProps {
  goal: SavingGoal | null;
  setGoal: (u: SavingGoal | null) => void;
  // 口座残高合計の計算に使う
  accounts: Account[];
  transactions: Tx[];
  incomes: Income[];
  transfers: Transfer[];
  // 削除確認ダイアログ
  ask: (title: string, msg: string, onOk: () => void) => void;
  showT: (msg: string, type?: string) => void;
}

export default function SavingGoalCard({
  goal,
  setGoal,
  accounts,
  transactions,
  incomes,
  transfers,
  ask,
  showT,
}: SavingGoalCardProps) {
  // 編集モーダル表示フラグ
  const [editing, setEditing] = useState(false);
  // 編集フォームの状態（名前・目標額・期限）
  const [form, setForm] = useState({ name: "", target: "", deadline: "" });

  // 現在の貯金額 = 全口座の残高合計
  const currentSaving = accounts.reduce(
    (sum, acc) => sum + calculateAccountBalance(acc, transactions, incomes, transfers),
    0
  );

  // 編集モーダルを開く（既存目標があれば値をセット、新規ならデフォルト値）
  function openEdit() {
    if (goal) {
      setForm({ name: goal.name, target: String(goal.targetAmount), deadline: goal.deadline });
    } else {
      // デフォルト期限：今日から1年後の月末
      const d = new Date();
      d.setFullYear(d.getFullYear() + 1);
      const defaultDeadline = `${d.getFullYear()}-12-31`;
      setForm({ name: "", target: "", deadline: defaultDeadline });
    }
    setEditing(true);
  }

  // 保存処理：入力値を検証して SavingGoal を作成・更新
  function save() {
    const target = parseYenAmount(form.target);
    if (!target || target <= 0) { showT("目標金額を入力してください", "error"); return; }
    if (!form.deadline) { showT("達成期限を選択してください", "error"); return; }
    if (goal) {
      // 既存目標の更新：startAmount は据え置き（ベースラインを変えない）
      setGoal({ ...goal, name: form.name || goal.name, targetAmount: target, deadline: form.deadline });
      showT("目標を更新しました");
    } else {
      // 新規作成：現在貯金額を startAmount として記録
      const today = new Date().toISOString().slice(0, 10);
      setGoal({
        id: newId(),
        name: form.name || "貯金目標",
        targetAmount: target,
        startAmount: currentSaving,
        deadline: form.deadline,
        createdAt: today,
      });
      showT("目標を設定しました");
    }
    setEditing(false);
  }

  // 削除：確認ダイアログを出してから null にする
  function remove() {
    ask("目標を削除しますか？", "進捗履歴も消えます。", () => {
      setGoal(null);
      showT("目標を削除しました", "error");
    });
  }

  // 目標未設定 & モーダル閉じている → CTA カード
  if (!goal && !editing) {
    return (
      <div style={STYLE_CARD}>
        <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 10 }}>
          🎯 貯金目標
        </div>
        <div style={{ fontSize: 13, color: COLOR_TEXT_SECONDARY, marginBottom: 12, lineHeight: 1.6 }}>
          目標を設定して、毎月いくら貯めれば達成できるかを可視化しましょう
        </div>
        <button onClick={openEdit} style={STYLE_BUTTON_PRIMARY}>＋ 目標を設定する</button>
      </div>
    );
  }

  // 進捗計算
  // 達成済み金額 = 現在貯金 - 目標設定時の貯金額（マイナスなら0扱い）
  const achieved = goal ? Math.max(0, currentSaving - goal.startAmount) : 0;
  // 目標までに増やす必要がある金額 = 目標額 - 目標設定時の貯金額
  const goalGap = goal ? Math.max(0, goal.targetAmount - goal.startAmount) : 0;
  // 達成率（%）
  const progress = goalGap > 0 ? Math.min(100, Math.round((achieved / goalGap) * 100)) : 100;
  // 残り必要金額（達成までいくら必要か）
  const remaining = goal ? Math.max(0, goal.targetAmount - currentSaving) : 0;
  // 期限までの残り月数（小数点切り上げ）
  const monthsLeft = goal ? Math.max(0, monthDiff(new Date(), new Date(goal.deadline))) : 0;
  // 月次必要貯金額（残り÷残り月数）
  const monthlyNeeded = monthsLeft > 0 ? Math.ceil(remaining / monthsLeft) : remaining;
  // 期限超過判定
  const overdue = goal ? new Date(goal.deadline) < new Date() && remaining > 0 : false;
  // 達成済み判定
  const achieved100 = goal && currentSaving >= goal.targetAmount;

  return (
    <>
      {/* メインの目標カード */}
      {goal && (
        <div style={{ ...STYLE_CARD, borderColor: achieved100 ? `${COLOR_POSITIVE}44` : overdue ? `${COLOR_NEGATIVE}44` : COLOR_BORDER }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 10, color: COLOR_TEXT_HINT, textTransform: "uppercase", letterSpacing: "1.5px", marginBottom: 4 }}>
                🎯 貯金目標
              </div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>{goal.name}</div>
              <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, marginTop: 2 }}>期限 {goal.deadline}</div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button onClick={openEdit} style={{ ...STYLE_BUTTON_OUTLINE, fontSize: 11, padding: "4px 10px", minHeight: 28 }}>編集</button>
              <button onClick={remove} style={{ ...STYLE_BUTTON_OUTLINE, fontSize: 11, padding: "4px 10px", minHeight: 28 }}>削除</button>
            </div>
          </div>

          {/* 進捗バー */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
            <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700 }}>
              {formatYen(currentSaving)} / {formatYen(goal.targetAmount)}
            </span>
            <span style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, color: achieved100 ? COLOR_POSITIVE : COLOR_ACCENT }}>
              {progress}%
            </span>
          </div>
          <div style={{ height: 8, background: "rgba(148,163,184,0.08)", borderRadius: 4, overflow: "hidden", marginBottom: 12 }}>
            <div style={{
              height: "100%",
              width: `${progress}%`,
              background: achieved100 ? COLOR_POSITIVE : overdue ? COLOR_NEGATIVE : COLOR_ACCENT,
              borderRadius: 4,
              transition: "width 0.4s ease",
            }} />
          </div>

          {/* 達成状況に応じてメッセージを切り替え */}
          {achieved100 ? (
            <div style={{ fontSize: 12, color: COLOR_POSITIVE, fontWeight: 600, textAlign: "center", padding: "6px 0" }}>
              🎉 目標達成おめでとうございます！
            </div>
          ) : (
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <div style={{ flex: 1, background: "rgba(148,163,184,0.05)", borderRadius: 10, padding: "10px 12px" }}>
                <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, letterSpacing: "1px", textTransform: "uppercase", marginBottom: 4 }}>残り</div>
                <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700 }}>{formatYen(remaining)}</div>
              </div>
              <div style={{ flex: 1, background: "rgba(148,163,184,0.05)", borderRadius: 10, padding: "10px 12px" }}>
                <div style={{ fontSize: 9, color: COLOR_TEXT_HINT, letterSpacing: "1px", textTransform: "uppercase", marginBottom: 4 }}>
                  {overdue ? "期限超過" : `あと${monthsLeft}ヶ月`}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 700, color: overdue ? COLOR_NEGATIVE : COLOR_TEXT_PRIMARY }}>
                  {overdue ? "—" : `月 ${formatYen(monthlyNeeded)}`}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 編集モーダル */}
      {editing && (
        <div onClick={() => setEditing(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.72)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
          <div onClick={e => e.stopPropagation()} style={{ background: "rgba(15,23,42,0.98)", border: `1px solid ${COLOR_BORDER}`, borderRadius: 22, padding: 24, width: "100%", maxWidth: 360, backdropFilter: "blur(20px)" }}>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>{goal ? "目標を編集" : "貯金目標を設定"}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
              <Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="目標名（例: 2026年末までに100万円）" />
              <Input money type="number" value={form.target} onChange={e => setForm(f => ({ ...f, target: e.target.value }))} placeholder="目標金額（円）" />
              <Input type="date" value={form.deadline} onChange={e => setForm(f => ({ ...f, deadline: e.target.value }))} />
            </div>
            {/* 新規設定時のみ：現在貯金額がベースラインになる旨を表示 */}
            {!goal && (
              <div style={{ fontSize: 11, color: COLOR_TEXT_HINT, marginBottom: 14, lineHeight: 1.5 }}>
                現在の貯金額（口座残高合計 {formatYen(currentSaving)}）をスタート地点として、ここからの増加分を進捗としてカウントします。
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setEditing(false)} style={{ ...STYLE_BUTTON_OUTLINE, flex: 1, minHeight: 44, padding: 12 }}>キャンセル</button>
              <button onClick={save} style={{ ...STYLE_BUTTON_PRIMARY, flex: 1 }}>保存</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// 2つの日付の差を月数で返す（小数点切り上げで月数を計算）
// 例: 2026/05/19 → 2026/12/31 なら 7ヶ月
function monthDiff(from: Date, to: Date): number {
  const years = to.getFullYear() - from.getFullYear();
  const months = to.getMonth() - from.getMonth();
  const total = years * 12 + months;
  // 日付の差を加味して月数を補正（月末締めで端数を切り上げ）
  return to.getDate() >= from.getDate() ? total : Math.max(0, total);
}
