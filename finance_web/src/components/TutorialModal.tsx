// ────────── チュートリアルモーダル ──────────
// 初回起動時に6ページのスライドでアプリの使い方を案内するモーダル
// open=false の時は何も描画しない

import { useState } from "react";
import { STYLE_BUTTON_PRIMARY } from "../utils/styles";

// 各ページの内容（アイコン・タイトル・説明文）
const PAGES = [
  {
    icon: "💰",
    title: "ようこそ！",
    desc: "このアプリは収入・支出・ローン・貯金目標をまとめて管理できる家計管理ツールです。データはすべてこの端末に暗号化保存されます。",
  },
  {
    icon: "💰",
    title: "収入タブ",
    desc: "給与・副業・ボーナスなどの収入を登録します。カテゴリごとに分類でき、月ごとの合計が自動集計されます。",
  },
  {
    icon: "📌",
    title: "固定費タブ",
    desc: "家賃・保険・サブスクなど毎月決まって出ていく費用を登録します。年払いも月割りで自動換算されます。",
  },
  {
    icon: "💸",
    title: "支出タブ",
    desc: "食費・交通費など変動する日々の出費を記録します。カテゴリ別に集計・グラフ表示されます。",
  },
  {
    icon: "🏦",
    title: "ローンタブ",
    desc: "住宅ローン・カーローンなどを登録し、返済シミュレーションができます。繰り上げ返済の効果も試算できます。",
  },
  {
    icon: "⚙️",
    title: "設定タブ",
    desc: "カテゴリの追加・編集・並び替えができます。データのバックアップ（JSON書き出し）と復元もここから行えます。",
  },
];

// このコンポーネントが受け取る props の型
interface TutorialModalProps {
  open: boolean;      // true = 表示、false = 非表示
  onClose: () => void; // 閉じる時に呼ばれる関数
}

export default function TutorialModal({ open, onClose }: TutorialModalProps) {
  // 現在表示中のページ番号（0〜5）
  const [page, setPage] = useState(0);

  // 閉じる時にページを0に戻す（useEffect不要のパターン）
  function handleClose() {
    setPage(0);
    onClose();
  }

  // open=false の時は何も描画しない
  if (!open) return null;

  const current = PAGES[page];         // 今表示するページのデータ
  const isLast = page === PAGES.length - 1; // 最終ページかどうか

  return (
    // 背景オーバーレイ（タップしても閉じない → 誤操作防止）
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0,0,0,0.72)",
      zIndex: 300,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
    }}>
      {/* モーダル本体 */}
      <div style={{
        background: "rgba(15,23,42,0.98)",
        border: "1px solid rgba(148,163,184,0.16)",
        borderRadius: 22,
        padding: "28px 24px 24px",
        width: "100%",
        maxWidth: 340,
        backdropFilter: "blur(20px)",
        position: "relative",
        textAlign: "center",
      }}>
        {/* ✕ 閉じるボタン（右上） */}
        <button
          aria-label="閉じる"
          onClick={handleClose}
          style={{
            position: "absolute",
            top: 14,
            right: 14,
            background: "none",
            border: "none",
            color: "rgba(255,255,255,0.4)",
            fontSize: 20,
            cursor: "pointer",
            lineHeight: 1,
            padding: 4,
            fontFamily: "inherit",
          }}
        >
          ✕
        </button>

        {/* ページアイコン（大） */}
        <div style={{ fontSize: 52, marginBottom: 16, lineHeight: 1 }}>
          {current.icon}
        </div>

        {/* タイトル */}
        <div style={{
          fontSize: 18,
          fontWeight: 700,
          color: "#f5f5f7",
          marginBottom: 12,
        }}>
          {current.title}
        </div>

        {/* 説明文 */}
        <div style={{
          fontSize: 13,
          color: "#9a9aa3",
          lineHeight: 1.7,
          marginBottom: 24,
          minHeight: 60,
        }}>
          {current.desc}
        </div>

        {/* ページドット（●○○…） */}
        <div style={{
          display: "flex",
          justifyContent: "center",
          gap: 6,
          marginBottom: 20,
        }}>
          {PAGES.map((_, i) => (
            <div
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: i === page ? "#818cf8" : "rgba(255,255,255,0.2)",
                transition: "background 0.2s ease",
              }}
            />
          ))}
        </div>

        {/* 次へ / はじめる ボタン */}
        <button
          onClick={() => {
            if (isLast) {
              handleClose();
            } else {
              setPage(p => p + 1);
            }
          }}
          style={{
            ...STYLE_BUTTON_PRIMARY,
            width: "100%",
            background: isLast ? "#34d399" : undefined,
            color: isLast ? "#0a0a0c" : undefined,
          }}
        >
          {isLast ? "はじめる" : "次へ"}
        </button>
      </div>
    </div>
  );
}
