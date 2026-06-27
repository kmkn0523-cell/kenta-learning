// ────────── UIヘルパの共有Context ──────────
// showT(トースト表示)/ask(確認ダイアログ)/delItem(削除＋元に戻す) は
// アプリ全体で1組だけ使う共通関数。これまで App.tsx から各Viewへ props で
// 延々と受け渡し（prop drilling）していたのを、Contextで一括共有して減らす。
// 値の出どころは useToast()（App.tsx）。型は useToast の実シグネチャに合わせる。
import { createContext, useContext, ReactNode } from "react";

export interface UIHelpers {
  // 画面上にトーストを出す（action付きで「元に戻す」ボタンも出せる）
  showT: (msg: string, type?: string, action?: { label: string; onClick: () => void }) => void;
  // 破壊操作の最終確認ダイアログを出す
  ask: (title: string, msg: string, onOk: () => void) => void;
  // 配列から要素を即削除し、Toastの「元に戻す」で復元できるようにする
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delItem: (id: string, setArr: (v: any) => void, label?: string) => void;
}

// Provider の外で使うと null。useUI 側で分かりやすいエラーにする
const UIHelpersContext = createContext<UIHelpers | null>(null);

// App がツリー上部で1回だけ置く。value に useToast の関数群を渡す
export function UIHelpersProvider({ value, children }: { value: UIHelpers; children: ReactNode }) {
  return <UIHelpersContext.Provider value={value}>{children}</UIHelpersContext.Provider>;
}

// 各コンポーネントから呼ぶフック。Provider の中でのみ使える
export function useUI(): UIHelpers {
  const ctx = useContext(UIHelpersContext);
  if (!ctx) throw new Error("useUI は UIHelpersProvider の中で使ってください");
  return ctx;
}
