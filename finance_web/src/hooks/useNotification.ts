// ────────── ブラウザ通知フック ──────────
// Web Notification API を使ってブラウザのローカル通知を送る
// PWA対応（サーバー不要）のため、アプリを開いている時だけ動作する

import { useCallback, useState } from "react";

// このフックが返す値の型
interface UseNotificationReturn {
  // 現在の通知許可状態（"default"=未決定 / "granted"=許可 / "denied"=拒否 / "unsupported"=非対応）
  permission: NotificationPermission | "unsupported";
  // ユーザーに通知の許可をリクエストする関数
  requestPermission: () => Promise<void>;
  // 通知を送る関数（許可されていない場合は何もしない）
  notify: (title: string, body?: string) => void;
}

export function useNotification(): UseNotificationReturn {
  // ブラウザが Notification API に対応しているか確認する
  const isSupported = typeof window !== "undefined" && "Notification" in window;

  // 許可状態を useState で管理（再レンダリングで UI に反映できるようにする）
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">(
    isSupported ? Notification.permission : "unsupported"
  );

  // 許可をリクエストする関数（「通知を有効にする」ボタンなどに紐づける）
  const requestPermission = useCallback(async () => {
    // 非対応環境では何もしない
    if (!isSupported) return;
    try {
      // ブラウザのポップアップで「許可/拒否」を求める
      const result = await Notification.requestPermission();
      // 結果を state に反映する
      setPermission(result);
    } catch {
      // 一部のブラウザ（古いSafariなど）でエラーになっても画面をクラッシュさせない
    }
  }, [isSupported]);

  // 実際に通知を送る関数
  const notify = useCallback((title: string, body?: string) => {
    // 非対応 or 許可されていない場合は何もしない
    if (!isSupported || Notification.permission !== "granted") return;
    try {
      // ブラウザ標準の通知を表示する
      new Notification(title, {
        body,
        // PWAのアイコンを使う（存在しなくてもエラーにならない）
        icon: "/icons/icon-192.png",
      });
    } catch {
      // 通知送信に失敗しても何もしない（通知はあくまで補助機能）
    }
  }, [isSupported]);

  return { permission, requestPermission, notify };
}
