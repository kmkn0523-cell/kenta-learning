// ────────── 同期マージエンジン（競合解決の中核） ──────────
// 設計書: docs/finance_web_sync_design_v2.md §3
// 2台の端末の家計データを、できるだけ自動でぶつからないように1つにまとめる純粋関数。
// ・配列データ（取引など）= id でユニオン。同じidは updatedAt が新しい方を採用
// ・削除 = トゥームストーン（削除済みidと削除時刻）で表現。削除より後に編集されたら復活
// ・単一値（予算など）= 新しい方を採用（last-write-wins）
// サーバ・ローカルどちらが「新しい」かは ISO8601 文字列の辞書順＝時系列で判定する

// 同期対象レコードの最低条件：一意なidと、任意の更新時刻
export interface SyncRecord {
  id: string;
  updatedAt?: string; // "YYYY-MM-DDTHH:mm:ss.sssZ"。無い場合は最古として扱う
  [key: string]: unknown;
}

// 削除済みを表す墓標
export interface Tombstone {
  id: string;
  deletedAt: string; // 削除した時刻（ISO8601）
}

// 単一値（予算・カテゴリ設定など）を更新時刻付きで包んだ形
export interface TimestampedValue<T> {
  value: T;
  updatedAt: string;
}

// 文字列の更新時刻を比較しやすいよう正規化する（未設定は最古＝""）
function ts(value?: string): string {
  return value || "";
}

// 2つのトゥームストーン配列をマージする（同じidは新しい削除時刻を残す）
export function mergeTombstones(local: Tombstone[], remote: Tombstone[]): Tombstone[] {
  const map = new Map<string, Tombstone>();
  for (const t of [...local, ...remote]) {
    const existing = map.get(t.id);
    // まだ無い、または今回の方が新しい削除なら上書き
    if (!existing || ts(t.deletedAt) > ts(existing.deletedAt)) map.set(t.id, t);
  }
  // id順で安定させて返す
  return [...map.values()].sort((a, b) => a.id.localeCompare(b.id));
}

// 配列データをマージする本体
// local/remote: 同種のレコード配列、tombstones: マージ済みの墓標一覧
// 戻り値: updatedAt 昇順→id順で安定ソートした配列（表示側は必要に応じて並べ替える前提）
export function mergeRecordArrays<T extends SyncRecord>(
  local: T[],
  remote: T[],
  tombstones: Tombstone[] = []
): T[] {
  // id → そのidの最新レコード（updatedAtが新しい方）
  const latest = new Map<string, T>();
  for (const rec of [...local, ...remote]) {
    const existing = latest.get(rec.id);
    if (!existing || ts(rec.updatedAt) >= ts(existing.updatedAt)) latest.set(rec.id, rec);
  }

  // id → 墓標の削除時刻
  const deletedAt = new Map<string, string>();
  for (const t of tombstones) {
    const cur = deletedAt.get(t.id);
    if (!cur || ts(t.deletedAt) > ts(cur)) deletedAt.set(t.id, t.deletedAt);
  }

  const result: T[] = [];
  for (const rec of latest.values()) {
    const del = deletedAt.get(rec.id);
    // 削除が編集と同時刻以降なら「削除が勝ち」＝表示しない。
    // 編集が削除より後（updatedAt > deletedAt）なら復活させる
    if (del !== undefined && ts(del) >= ts(rec.updatedAt)) continue;
    result.push(rec);
  }

  // 安定した順序で返す（updatedAt 昇順→id）
  result.sort((a, b) => {
    const d = ts(a.updatedAt).localeCompare(ts(b.updatedAt));
    return d !== 0 ? d : a.id.localeCompare(b.id);
  });
  return result;
}

// 単一値をマージする。新しい方を採用しつつ「両方が基準時刻より後に変わったか＝衝突」を返す。
// baseUpdatedAt: 前回同期した時点の更新時刻（あれば衝突検出に使う。無ければ純粋なLWW）
export function mergeSingleton<T>(
  local: TimestampedValue<T>,
  remote: TimestampedValue<T>,
  baseUpdatedAt?: string
): { merged: TimestampedValue<T>; conflict: boolean; winner: "local" | "remote" | "equal" } {
  const l = ts(local.updatedAt);
  const r = ts(remote.updatedAt);

  // 衝突判定：基準より後に両方変わっていて、かつ中身が違うとき
  const base = ts(baseUpdatedAt);
  const bothChanged = baseUpdatedAt !== undefined && l > base && r > base;
  const conflict = bothChanged && JSON.stringify(local.value) !== JSON.stringify(remote.value);

  // 採用は新しい方（同時刻なら remote を優先＝サーバ寄りで安定）
  if (l > r) return { merged: local, conflict, winner: "local" };
  if (r > l) return { merged: remote, conflict, winner: "remote" };
  return { merged: remote, conflict, winner: "equal" };
}
