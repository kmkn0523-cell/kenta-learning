// ────────── 同期マージエンジンのテスト ──────────
// 設計の肝「2端末の家計データを自動で安全にまとめる」を実証する
// 設計書: docs/finance_web_sync_design_v2.md §3
import { describe, it, expect } from "vitest";
import {
  mergeRecordArrays,
  mergeTombstones,
  mergeSingleton,
  SyncRecord,
  Tombstone,
} from "./syncMerge";

// テスト用のレコード生成ヘルパー
function rec(id: string, updatedAt: string, extra: Record<string, unknown> = {}): SyncRecord {
  return { id, updatedAt, ...extra };
}
const ids = (items: { id: string }[]) => items.map(i => i.id).sort();

describe("mergeRecordArrays（配列のユニオンマージ）", () => {
  it("別々の追加は両方残る（端末Aで食費・端末Bで家賃）", () => {
    const local = [rec("a", "2026-06-01T10:00:00Z", { name: "食費" })];
    const remote = [rec("b", "2026-06-01T11:00:00Z", { name: "家賃" })];
    expect(ids(mergeRecordArrays(local, remote))).toEqual(["a", "b"]);
  });

  it("同じidは updatedAt が新しい方を採用する", () => {
    const local = [rec("a", "2026-06-01T10:00:00Z", { amount: 100 })];
    const remote = [rec("a", "2026-06-02T10:00:00Z", { amount: 999 })];
    const merged = mergeRecordArrays(local, remote);
    expect(merged.length).toBe(1);
    expect(merged[0].amount).toBe(999);
  });

  it("重複なくマージされる（同一データが両方にあっても1件）", () => {
    const same = [rec("a", "2026-06-01T10:00:00Z")];
    expect(mergeRecordArrays(same, same).length).toBe(1);
  });

  it("トゥームストーンがあるidは削除される", () => {
    const local = [rec("a", "2026-06-01T10:00:00Z"), rec("b", "2026-06-01T10:00:00Z")];
    const tomb: Tombstone[] = [{ id: "a", deletedAt: "2026-06-02T10:00:00Z" }];
    expect(ids(mergeRecordArrays(local, [], tomb))).toEqual(["b"]);
  });

  it("削除より後に編集されたレコードは復活する（resurrection）", () => {
    // 削除(6/2)より編集(6/3)が新しい → 残す
    const local = [rec("a", "2026-06-03T10:00:00Z", { amount: 500 })];
    const tomb: Tombstone[] = [{ id: "a", deletedAt: "2026-06-02T10:00:00Z" }];
    const merged = mergeRecordArrays(local, [], tomb);
    expect(merged.length).toBe(1);
    expect(merged[0].amount).toBe(500);
  });

  it("削除と編集が同時刻なら削除が勝つ（安全側）", () => {
    const local = [rec("a", "2026-06-02T10:00:00Z")];
    const tomb: Tombstone[] = [{ id: "a", deletedAt: "2026-06-02T10:00:00Z" }];
    expect(mergeRecordArrays(local, [], tomb).length).toBe(0);
  });

  it("updatedAt が無いレコードは最古として扱う（既存データの互換）", () => {
    const local = [{ id: "a", amount: 1 } as SyncRecord];
    const remote = [rec("a", "2026-06-01T10:00:00Z", { amount: 2 })];
    // remote の方が新しい扱い
    expect(mergeRecordArrays(local, remote)[0].amount).toBe(2);
  });

  it("結果は updatedAt昇順→id順で安定している（呼ぶたびに同じ並び）", () => {
    const local = [rec("b", "2026-06-02T00:00:00Z"), rec("a", "2026-06-01T00:00:00Z")];
    const remote = [rec("c", "2026-06-03T00:00:00Z")];
    const r1 = mergeRecordArrays(local, remote).map(x => x.id);
    const r2 = mergeRecordArrays(remote, local).map(x => x.id);
    expect(r1).toEqual(["a", "b", "c"]);
    expect(r1).toEqual(r2); // 入力順を入れ替えても同じ結果
  });
});

describe("mergeTombstones（墓標のマージ）", () => {
  it("同じidは新しい削除時刻を残す", () => {
    const local: Tombstone[] = [{ id: "a", deletedAt: "2026-06-01T00:00:00Z" }];
    const remote: Tombstone[] = [{ id: "a", deletedAt: "2026-06-05T00:00:00Z" }];
    const merged = mergeTombstones(local, remote);
    expect(merged.length).toBe(1);
    expect(merged[0].deletedAt).toBe("2026-06-05T00:00:00Z");
  });

  it("別idはすべて残る", () => {
    const local: Tombstone[] = [{ id: "a", deletedAt: "2026-06-01T00:00:00Z" }];
    const remote: Tombstone[] = [{ id: "b", deletedAt: "2026-06-01T00:00:00Z" }];
    expect(ids(mergeTombstones(local, remote))).toEqual(["a", "b"]);
  });
});

describe("mergeSingleton（単一値の last-write-wins ＋衝突検出）", () => {
  it("新しい方を採用する", () => {
    const local = { value: { food: 30000 }, updatedAt: "2026-06-01T00:00:00Z" };
    const remote = { value: { food: 50000 }, updatedAt: "2026-06-02T00:00:00Z" };
    const r = mergeSingleton(local, remote);
    expect(r.merged.value).toEqual({ food: 50000 });
    expect(r.winner).toBe("remote");
  });

  it("基準時刻より後に両方が別々に変わったら衝突フラグが立つ", () => {
    const base = "2026-06-01T00:00:00Z";
    const local = { value: { food: 30000 }, updatedAt: "2026-06-02T00:00:00Z" };
    const remote = { value: { food: 50000 }, updatedAt: "2026-06-03T00:00:00Z" };
    const r = mergeSingleton(local, remote, base);
    expect(r.conflict).toBe(true);   // 3択UIを出す合図
    expect(r.merged.value).toEqual({ food: 50000 }); // それでも採用は新しい方
  });

  it("片方しか変わっていなければ衝突ではない", () => {
    const base = "2026-06-02T00:00:00Z";
    const local = { value: { food: 30000 }, updatedAt: "2026-06-01T00:00:00Z" }; // 基準より前
    const remote = { value: { food: 50000 }, updatedAt: "2026-06-03T00:00:00Z" };
    expect(mergeSingleton(local, remote, base).conflict).toBe(false);
  });

  it("中身が同じなら衝突ではない（両方変わっていても）", () => {
    const base = "2026-06-01T00:00:00Z";
    const same = { food: 40000 };
    const local = { value: same, updatedAt: "2026-06-02T00:00:00Z" };
    const remote = { value: same, updatedAt: "2026-06-03T00:00:00Z" };
    expect(mergeSingleton(local, remote, base).conflict).toBe(false);
  });
});
