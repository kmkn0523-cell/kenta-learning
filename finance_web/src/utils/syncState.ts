// ────────── 同期ステート（全データの集約・マージ・適用） ──────────
// 設計書: docs/finance_web_sync_design_v2.md §3。
// アプリ内の複数の localStorage(kk_*) を「1つの同期ペイロード」にまとめ、
// 別端末のペイロードと突き合わせてマージし、また各 kk_* に戻すための純粋関数群。
// React やネットワークには依存しない（＝単体テストしやすい）。
import {
  mergeRecordArrays,
  mergeSingleton,
  mergeTombstones,
  type Tombstone,
  type SyncRecord,
} from "./syncMerge";

// 同期対象キーの種類
// - "array"     : id付きレコードの配列（取引・収入など）。id＋updatedAtでユニオンマージ
// - "singleton" : 単一の値（予算・カテゴリ設定・貯金目標）。新しい方を採用＝LWW、衝突は別途検知
export type SyncableKind = "array" | "singleton";

export interface SyncKeyDef {
  key: string;
  kind: SyncableKind;
}

// 同期する全キーの一覧（設計書§3の同期対象）
export const SYNC_KEYS: SyncKeyDef[] = [
  { key: "kk_tx", kind: "array" },
  { key: "kk_inc", kind: "array" },
  { key: "kk_fx", kind: "array" },
  { key: "kk_lo", kind: "array" },
  { key: "kk_cf", kind: "array" },
  { key: "kk_bl", kind: "array" },
  { key: "kk_accounts", kind: "array" },
  { key: "kk_transfers", kind: "array" },
  { key: "kk_tpls", kind: "array" },
  { key: "kk_rec_inc", kind: "array" },
  { key: "kk_rec_exp", kind: "array" },
  { key: "kk_budget", kind: "singleton" },
  { key: "kk_categories", kind: "singleton" },
  { key: "kk_savingGoal", kind: "singleton" },
];

const ARRAY_KEYS = SYNC_KEYS.filter(k => k.kind === "array").map(k => k.key);
const SINGLETON_KEYS = SYNC_KEYS.filter(k => k.kind === "singleton").map(k => k.key);

// 各 kk_* の現在値をまとめた箱。値の型は呼び出し側次第なので unknown で受ける。
export type SyncValues = Record<string, unknown>;

// 単一値が「いつ変わったか」を覚えておくメタ情報（衝突検知に使う）
export type SingletonMeta = Record<string, string>; // key -> ISO8601

// サーバとやり取りする同期ペイロードの形（暗号化前の中身）
export interface SyncState {
  values: SyncValues;          // kk_* の値
  tombstones: Tombstone[];     // 削除済みレコードの墓標
  singletonMeta: SingletonMeta; // 単一値の最終更新時刻
}

// 競合した単一値の「この端末の値」と「別端末の値」。ユーザーがどちらを残すか選ぶのに使う。
export interface ConflictDetail {
  key: string;     // kk_budget など
  local: unknown;  // この端末の値
  remote: unknown; // 別端末の値
}

// 空の同期ステート
export function emptySyncState(): SyncState {
  return { values: {}, tombstones: [], singletonMeta: {} };
}

// 現在のアプリ状態から同期ステートを組み立てる。
// prev: 前回pushした同期ステート（単一値が変わったかの比較に使う。無ければ全部「今」を採用）
// now:  現在時刻(ISO8601)
export function buildSyncState(
  current: SyncValues,
  prev: SyncState | null,
  tombstones: Tombstone[],
  now: string
): SyncState {
  const singletonMeta: SingletonMeta = { ...(prev?.singletonMeta ?? {}) };
  for (const key of SINGLETON_KEYS) {
    const prevVal = prev?.values[key];
    const curVal = current[key];
    const changed = JSON.stringify(prevVal) !== JSON.stringify(curVal);
    // 前回pushから中身が変わっていれば「今」更新したことにする。変わっていなければ前回の時刻を保つ。
    if (changed || !singletonMeta[key]) singletonMeta[key] = now;
  }
  return { values: { ...current }, tombstones, singletonMeta };
}

// 前回同期(base)に有ったのに今(current)で消えているレコードを「削除された」と判定し、
// 墓標(トゥームストーン)に積む。各削除箇所のコードを触らずに削除を同期できる。
export function detectTombstones(
  base: SyncState | null,
  current: SyncValues,
  existing: Tombstone[],
  now: string
): Tombstone[] {
  if (!base) return existing;
  const seen = new Set(existing.map(t => t.id));
  const result = [...existing];
  for (const key of ARRAY_KEYS) {
    const baseArr = Array.isArray(base.values[key]) ? (base.values[key] as { id: string }[]) : [];
    const curArr = Array.isArray(current[key]) ? (current[key] as { id: string }[]) : [];
    const curIds = new Set(curArr.map(r => r.id));
    for (const rec of baseArr) {
      if (rec && rec.id && !curIds.has(rec.id) && !seen.has(rec.id)) {
        result.push({ id: rec.id, deletedAt: now });
        seen.add(rec.id);
      }
    }
  }
  return result;
}

// ローカルとリモートの同期ステートをマージする。
// base: 前回同期した時点のステート（単一値の衝突検知に使う。無ければ純粋LWW）
// 戻り値: マージ後ステートと、3択が必要な単一値キーの一覧(conflicts)
export function mergeSyncState(
  local: SyncState,
  remote: SyncState,
  base?: SyncState | null
): { merged: SyncState; conflicts: string[]; conflictDetails: ConflictDetail[] } {
  const tombstones = mergeTombstones(local.tombstones, remote.tombstones);
  const values: SyncValues = {};
  const conflicts: string[] = [];
  const conflictDetails: ConflictDetail[] = [];

  // 配列系：id＋updatedAtでユニオンマージ
  for (const key of ARRAY_KEYS) {
    const l = Array.isArray(local.values[key]) ? (local.values[key] as SyncRecord[]) : [];
    const r = Array.isArray(remote.values[key]) ? (remote.values[key] as SyncRecord[]) : [];
    values[key] = mergeRecordArrays(l, r, tombstones);
  }

  // 単一値系：新しい方を採用。両端末がbase以降に変えていたら衝突として記録
  const singletonMeta: SingletonMeta = {};
  for (const key of SINGLETON_KEYS) {
    const lTime = local.singletonMeta[key] ?? "";
    const rTime = remote.singletonMeta[key] ?? "";
    const baseTime = base?.singletonMeta[key];
    const res = mergeSingleton(
      { value: local.values[key], updatedAt: lTime },
      { value: remote.values[key], updatedAt: rTime },
      baseTime
    );
    values[key] = res.merged.value;
    singletonMeta[key] = res.merged.updatedAt;
    if (res.conflict) {
      conflicts.push(key);
      conflictDetails.push({ key, local: local.values[key], remote: remote.values[key] });
    }
  }

  return { merged: { values, tombstones, singletonMeta }, conflicts, conflictDetails };
}
