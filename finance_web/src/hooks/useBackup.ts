// ────────── バックアップ・復元の共通ロジック ──────────
// localStorage の暗号化済みデータをJSONファイルに書き出す／書き戻すユーティリティを提供する
// 中身は暗号化済みのまま扱うのでファイルが漏れてもパスワードがないと復号できない

import { ENC_SALT_KEY } from "../utils/crypto";

// バックアップ対象の localStorage キー（家計データ13種 + 暗号化salt）
// ※新しい永続化キーを増やす場合はここに追加すること
const BACKUP_KEYS = [
  "kk_tx",          // 変動支出
  "kk_fx",          // 固定費
  "kk_lo",          // ローン
  "kk_cf",          // キャッシング
  "kk_bl",          // 銀行ローン
  "kk_inc",         // 収入
  "kk_accounts",    // 口座
  "kk_budget",      // 予算
  "kk_tpls",        // テンプレート
  "kk_transfers",   // 口座間振替
  "kk_categories",  // カテゴリ設定（ユーザーカスタマイズ）
  "kk_savingGoal",  // 貯金目標
  "kk_rec_inc",     // 定期収入設定
  "kk_rec_exp",     // 定期支出設定（繰り返し変動費）
  ENC_SALT_KEY,     // 暗号化用salt
];

interface UseBackupArgs {
  // ファイル名の日付サフィックスに使う今日の日付（YYYY-MM-DD）
  todayStr: string;
  // 操作結果を伝えるトースト関数
  showT: (msg: string, type?: string) => void;
  // 復元時の上書き確認ダイアログを出す関数
  ask: (title: string, msg: string, onOk: () => void) => void;
}

export function useBackup({ todayStr, showT, ask }: UseBackupArgs) {
  // ────────── バックアップ：家計データを丸ごとJSONファイルへ書き出す ──────────
  // 暗号化済みの文字列をそのまま入れ物に詰めて、JSONファイルとしてダウンロードする
  function exportBackup() {
    try {
      const data: Record<string, string> = {};
      for (const k of BACKUP_KEYS) {
        const v = localStorage.getItem(k);
        if (v !== null) data[k] = v;
      }
      // バージョン番号と書き出し日時もメタ情報として一緒に入れる
      const payload = { version: 1, encrypted: true, exportedAt: new Date().toISOString(), data };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `家計バックアップ_${todayStr}.json`;
      a.click();
      URL.revokeObjectURL(url);
      showT("バックアップを保存しました");
    } catch (_) {
      showT("バックアップに失敗しました", "error");
    }
  }

  // ────────── 復元：バックアップJSONを読み込んで localStorage に書き戻す ──────────
  // 同じパスワードでないと復号できない（saltも一緒に復元されるので同じパスワードならOK）
  function importBackup(file: File) {
    // 10MB超えのファイルは不正データの可能性があるため拒否
    if (file.size > 10 * 1024 * 1024) {
      showT("ファイルサイズが大きすぎます（10MB以下）", "error");
      return;
    }
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const obj = JSON.parse(e.target?.result as string);
        if (!obj || typeof obj.data !== "object" || obj.data === null) {
          showT("ファイル形式が違います", "error");
          return;
        }
        // 上書き前にユーザーに最終確認
        ask("バックアップから復元しますか？", "現在のデータが上書きされ、ページが再読み込みされます。", () => {
          try {
            for (const [k, v] of Object.entries(obj.data)) {
              // 想定しているキーだけ書き戻す（変なキーが混じっていても無視）
              if (BACKUP_KEYS.includes(k) && typeof v === "string") {
                localStorage.setItem(k, v);
              }
            }
            showT("復元しました。再読み込みします");
            // パスワード再入力を経て鍵を派生し直すため、少し待ってからリロード
            setTimeout(() => {
              try { sessionStorage.removeItem("ff_auth"); }
              catch (error) { console.warn("[useBackup] sessionStorage clear failed", error); }
              window.location.reload();
            }, 800);
          } catch (_) {
            showT("復元に失敗しました", "error");
          }
        });
      } catch (_) {
        showT("ファイルを読み込めませんでした", "error");
      }
    };
    reader.readAsText(file);
  }

  return { exportBackup, importBackup };
}
