// ────────── トースト・確認ダイアログ・削除Undo の共通ロジック ──────────
// アプリ全体で使う通知系をひとまとめにする
// - showT(msg, type?, action?): 画面上に通知を表示（actionを渡すと「元に戻す」ボタン付き）
// - ask(title, msg, onOk): 確認ダイアログを表示（破壊操作で使う）
// - delItem(id, setArr, label?): 配列から要素を即削除しつつToastに「元に戻す」を出す

import { useState, useCallback, useRef } from "react";

// Toast のデータ形（ui.tsx の ToastData と一致させる）
export interface ToastData {
  msg: string;
  type?: "success" | "error" | "info";
  action?: { label: string; onClick: () => void };
}

// 確認ダイアログのデータ形
export interface DialogData {
  title: string;
  msg?: string;
  onOk: () => void;
}

export function useToast() {
  // 表示中のトースト・ダイアログ（null＝非表示）
  const [toast, setToast] = useState<ToastData | null>(null);
  const [dlg, setDlg] = useState<DialogData | null>(null);
  // 自動消去タイマーのID（連続表示時に前のタイマーをキャンセルするため保持）
  const tr = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 通知を表示する。action付き=5秒、それ以外=2.2秒で自動消去
  const showT = useCallback((msg: string, type?: string, action?: { label: string; onClick: () => void }) => {
    if (tr.current) clearTimeout(tr.current);
    setToast({ msg, type: (type || "success") as ToastData["type"], action });
    tr.current = setTimeout(() => setToast(null), action ? 5000 : 2200);
  }, []);

  // 確認ダイアログを開く（破壊操作の最終確認に使う）
  const ask = useCallback((title: string, msg: string, onOk: () => void) => {
    setDlg({ title, msg, onOk });
  }, []);

  // 配列から要素を即削除し、Toast の「元に戻す」で復元できるようにする（Gmail方式）
  // setter callback の中で snapshot を確保し、setTimeout で次tickにToastを出す（updater内副作用を回避）
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const delItem = useCallback((id: string, setArr: (v: any) => void, label?: string) => {
    setArr((prev: { id: string }[]) => {
      const snapshot = prev;
      setTimeout(() => {
        showT(label || "削除しました", "error", {
          label: "元に戻す",
          onClick: () => { setArr(snapshot); showT("元に戻しました"); },
        });
      }, 0);
      return prev.filter(x => x.id !== id);
    });
  }, [showT]);

  return { toast, dlg, setDlg, showT, ask, delItem };
}
