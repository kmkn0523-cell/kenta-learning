// ────────── クラウド同期フック ──────────
// 設計書: docs/finance_web_sync_design_v2.md §4-5。
// 役割: 復元キー(RK)から accountId と データ鍵(DEK)を導出し、
//   ・ローカル変更を 5秒 debounce してサーバへ push
//   ・30秒ごとにサーバを poll して pull→マージ→ローカル反映
//   ・版番号(version)で楽観ロック。409 が返ったらマージして再push
// サーバは中身を読めない（DEKで暗号化＝E2E）。
import { useState, useEffect, useRef, useCallback } from "react";
import {
  parseRecoveryKey,
  deriveAccountId,
  deriveDataKey,
  encryptValue,
  decryptValue,
} from "../utils/crypto";
import {
  buildSyncState,
  mergeSyncState,
  detectTombstones,
  emptySyncState,
  SYNC_KEYS,
  type SyncState,
  type SyncValues,
} from "../utils/syncState";
import type { Tombstone } from "../utils/syncMerge";

// 同期状態を画面に出すためのステータス
export type SyncStatus = "off" | "idle" | "syncing" | "error" | "conflict";

// localStorage に同期メタを置くキー
const LS_RK_WRAPPED = "kk_sync_rk_wrapped"; // パスワードで包んだRK（端末ローカル保存）
const LS_VERSION = "kk_sync_version";        // 最後にサーバと合わせた版番号
const LS_BASE = "kk_sync_base";              // 前回同期したステート（衝突検知の基準）
const LS_TOMBSTONES = "kk_tombstones";       // 削除済みレコードの墓標

const DEBOUNCE_MS = 5000;
const POLL_MS = 30000;

// フックに渡す依存：各 kk_* の「今の値」と「セッター」
export interface CloudSyncDeps {
  // 現在値を取り出す関数（呼ぶたび最新の値を返すこと）
  getValues: () => SyncValues;
  // マージ結果を各ストアへ書き戻すセッター（key → setter）
  setters: Record<string, (value: unknown) => void>;
  // 同期が有効に「なれる」状態か（パスワード解錠後＝allOk）
  ready: boolean;
}

// localStorage から JSON を安全に読む
function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function useCloudSync({ getValues, setters, ready }: CloudSyncDeps) {
  const [status, setStatus] = useState<SyncStatus>("off");
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<string[]>([]);

  // RK由来の秘密はメモリ上のrefに持つ（再レンダーで作り直さない）
  const accountIdRef = useRef<string | null>(null);
  const dekRef = useRef<CryptoKey | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const enabledRef = useRef(false);

  // 起動時：RKがwrap保存されていれば「同期ON」とみなす（解錠は activate で行う）
  useEffect(() => {
    if (localStorage.getItem(LS_RK_WRAPPED)) setStatus(s => (s === "off" ? "idle" : s));
  }, []);

  // RK(Uint8Array)から accountId と DEK を導出してメモリに載せる
  const loadKeys = useCallback(async (rk: Uint8Array) => {
    accountIdRef.current = await deriveAccountId(rk);
    dekRef.current = await deriveDataKey(rk);
    enabledRef.current = true;
  }, []);

  // サーバから1回 pull してローカルとマージ→反映。必要なら push まで行う。
  const syncOnce = useCallback(async () => {
    if (!enabledRef.current || !accountIdRef.current || !dekRef.current) return;
    const accountId = accountIdRef.current;
    const dek = dekRef.current;
    setStatus("syncing");
    try {
      // 1) サーバ最新を取得
      const res = await fetch(`/api/sync?accountId=${encodeURIComponent(accountId)}`);
      if (res.status === 402) { setStatus("error"); return; } // 課金切れ
      if (!res.ok) { setStatus("error"); return; }
      const envelope = (await res.json()) as { version: number; data: string } | null;

      // 2) リモートを復号（無ければ空ステート）
      let remote: SyncState = emptySyncState();
      let serverVersion = 0;
      if (envelope) {
        serverVersion = envelope.version;
        remote = (await decryptValue(dek, envelope.data)) as SyncState;
      }

      // 3) ローカルの今の状態を組み立てる（消えたレコードはトゥームストーンに自動記録）
      const now = new Date().toISOString();
      const prevBase = readJson<SyncState | null>(LS_BASE, null);
      const currentValues = getValues();
      const tombstones = detectTombstones(
        prevBase,
        currentValues,
        readJson<Tombstone[]>(LS_TOMBSTONES, []),
        now
      );
      const local = buildSyncState(currentValues, prevBase, tombstones, now);

      // 4) マージ
      const { merged, conflicts: conf } = mergeSyncState(local, remote, prevBase);
      setConflicts(conf);

      // 5) マージ結果をローカルへ反映（各セッターを呼ぶ）
      for (const { key } of SYNC_KEYS) {
        if (key in merged.values && setters[key]) setters[key](merged.values[key]);
      }
      localStorage.setItem(LS_TOMBSTONES, JSON.stringify(merged.tombstones));

      // 6) サーバへ push（楽観ロック）。409なら次回 poll で再試行。
      const data = await encryptValue(dek, merged);
      const putRes = await fetch("/api/sync", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accountId, version: serverVersion, data }),
      });
      if (putRes.status === 200) {
        const body = (await putRes.json()) as { version: number; updatedAt: string };
        localStorage.setItem(LS_VERSION, String(body.version));
        localStorage.setItem(LS_BASE, JSON.stringify(merged));
        setLastSyncedAt(body.updatedAt);
        setStatus(conf.length > 0 ? "conflict" : "idle");
      } else if (putRes.status === 409) {
        // 別端末が先に書いた → 次回 poll で取り直してマージ
        setStatus("idle");
      } else if (putRes.status === 402) {
        setStatus("error");
      } else {
        setStatus("error");
      }
    } catch (error) {
      console.warn("[useCloudSync] syncOnce failed", error);
      setStatus("error");
    }
  }, [getValues, setters]);

  // 同期を有効化（RK文字列＋パスワードで解錠して保存）
  const activate = useCallback(async (rkDisplay: string) => {
    const rk = parseRecoveryKey(rkDisplay);
    if (!rk) throw new Error("復元キーの形式が正しくありません");
    await loadKeys(rk);
    setStatus("idle");
    await syncOnce();
  }, [loadKeys, syncOnce]);

  // 同期を停止（ローカルの鍵・メタを消す。サーバのデータは残す）
  const deactivate = useCallback(() => {
    enabledRef.current = false;
    accountIdRef.current = null;
    dekRef.current = null;
    localStorage.removeItem(LS_RK_WRAPPED);
    localStorage.removeItem(LS_VERSION);
    localStorage.removeItem(LS_BASE);
    setStatus("off");
    setLastSyncedAt(null);
  }, []);

  // ローカル変更を検知して 5秒 debounce で push（呼び出し側が変更時にこれを叩く）
  const notifyChange = useCallback(() => {
    if (!enabledRef.current) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { void syncOnce(); }, DEBOUNCE_MS);
  }, [syncOnce]);

  // 30秒ごとの定期 poll
  useEffect(() => {
    if (!ready) return;
    const timer = setInterval(() => {
      if (enabledRef.current) void syncOnce();
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [ready, syncOnce]);

  return {
    status,
    lastSyncedAt,
    conflicts,
    isEnabled: enabledRef.current,
    activate,
    deactivate,
    notifyChange,
    syncNow: syncOnce,
  };
}
