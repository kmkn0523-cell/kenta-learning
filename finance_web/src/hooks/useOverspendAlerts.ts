// ────────── 使いすぎアラート・フック ──────────
// 当月のカテゴリ別支出が変わるたびに判定し、新たに閾値を超えたら通知する。
// 判定ロジックは純粋関数(evaluateOverspend)に委ね、ここは「監視→通知→保存」だけ担う。
import { useEffect } from "react";
import { evaluateOverspend, pruneLog, type NotifyLog, type OverspendAlert } from "../utils/overspendAlerts";
import { formatYen } from "../utils/format";

// localStorage に通知ログを置くキー（端末ローカル・同期しない）
const LS_LOG = "kk_notify_overspend_log";

export interface UseOverspendAlertsDeps {
  enabled: boolean;                                    // 設定スイッチ
  permission: NotificationPermission | "unsupported"; // 通知許可状態
  actualByCategory: Record<string, number>;           // 当月のカテゴリ別支出
  budget: Record<string, number>;                     // カテゴリ別予算
  notify: (title: string, body?: string) => void;     // 通知関数（useNotification由来）
  ready: boolean;                                      // データ読込完了フラグ
}

// localStorage から通知ログを安全に読む
function readLog(): NotifyLog {
  try {
    const raw = localStorage.getItem(LS_LOG);
    return raw ? (JSON.parse(raw) as NotifyLog) : {};
  } catch {
    return {};
  }
}

// 1件のアラートを通知文言にする
function alertToMessage(alert: OverspendAlert): { title: string; body: string } {
  const percent = Math.round(alert.ratio * 100);
  if (alert.level === 100) {
    // 予算オーバー：超過額も出す
    const over = alert.spent - alert.budget;
    return {
      title: `🚨 ${alert.category}が予算オーバー`,
      body: `今月 ${formatYen(alert.spent)} / ${formatYen(alert.budget)}（${formatYen(over)}超過）`,
    };
  }
  // 80%注意
  return {
    title: `⚠️ ${alert.category}が予算の${percent}%`,
    body: `今月 ${formatYen(alert.spent)} / ${formatYen(alert.budget)}`,
  };
}

export function useOverspendAlerts(deps: UseOverspendAlertsDeps): void {
  const { enabled, permission, actualByCategory, budget, notify, ready } = deps;

  // 当月支出が変わるたび（＝支出記録時）と初回（＝アプリ起動時）に判定する
  useEffect(() => {
    // データ未読込・スイッチオフ・未許可なら何もしない
    if (!ready || !enabled || permission !== "granted") return;

    // 当月("YYYY-MM")を求める
    const now = new Date();
    const month = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0");

    // 既存ログを当月だけに掃除してから判定
    const log = pruneLog(readLog(), month);
    const { alerts, nextLog } = evaluateOverspend(actualByCategory, budget, log, month);

    if (alerts.length === 1) {
      // 1件：具体的に通知
      const { title, body } = alertToMessage(alerts[0]);
      notify(title, body);
    } else if (alerts.length > 1) {
      // 複数：連発を避けて1件に集約
      const overCount = alerts.filter(a => a.level === 100).length;
      const summary = overCount > 0
        ? `${alerts.length}件のカテゴリが予算に近づく/超えています`
        : `${alerts.length}件のカテゴリが予算に近づいています`;
      notify("⚠️ 予算アラート", summary);
    }

    // 鳴らした分を記録（次回以降の二重通知を防ぐ）
    if (alerts.length > 0) {
      try {
        localStorage.setItem(LS_LOG, JSON.stringify(nextLog));
      } catch {
        // 保存失敗は致命的でないので無視
      }
    }
    // actualByCategory / budget / enabled / permission / ready の変化で再評価
  }, [ready, enabled, permission, actualByCategory, budget, notify]);
}
