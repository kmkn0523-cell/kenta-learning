import { describe, it, expect } from "vitest";
import {
  buildSyncState,
  mergeSyncState,
  detectTombstones,
  emptySyncState,
  SYNC_KEYS,
} from "../../utils/syncState";

const NOW = "2026-06-22T12:00:00.000Z";
const EARLIER = "2026-06-22T10:00:00.000Z";
const LATER = "2026-06-22T14:00:00.000Z";

describe("buildSyncState", () => {
  it("単一値が前回から変わっていたら updatedAt を now にする", () => {
    const prev = buildSyncState({ kk_budget: { food: 100 } }, null, [], EARLIER);
    const next = buildSyncState({ kk_budget: { food: 200 } }, prev, [], NOW);
    expect(next.singletonMeta.kk_budget).toBe(NOW);
  });

  it("単一値が変わっていなければ前回の時刻を保つ", () => {
    const prev = buildSyncState({ kk_budget: { food: 100 } }, null, [], EARLIER);
    const next = buildSyncState({ kk_budget: { food: 100 } }, prev, [], NOW);
    expect(next.singletonMeta.kk_budget).toBe(EARLIER);
  });

  it("values と tombstones をそのまま格納する", () => {
    const tomb = [{ id: "x", deletedAt: NOW }];
    const s = buildSyncState({ kk_tx: [{ id: "1" }] }, null, tomb, NOW);
    expect(s.values.kk_tx).toEqual([{ id: "1" }]);
    expect(s.tombstones).toEqual(tomb);
  });
});

describe("mergeSyncState 配列", () => {
  it("両端末で別レコードを追加したら両方残る", () => {
    const local = buildSyncState({ kk_tx: [{ id: "a", updatedAt: NOW }] }, null, [], NOW);
    const remote = buildSyncState({ kk_tx: [{ id: "b", updatedAt: NOW }] }, null, [], NOW);
    const { merged } = mergeSyncState(local, remote);
    const ids = (merged.values.kk_tx as { id: string }[]).map(r => r.id).sort();
    expect(ids).toEqual(["a", "b"]);
  });

  it("同じidは updatedAt が新しい方を採用する", () => {
    const local = buildSyncState({ kk_tx: [{ id: "a", amount: 1, updatedAt: EARLIER }] }, null, [], NOW);
    const remote = buildSyncState({ kk_tx: [{ id: "a", amount: 2, updatedAt: LATER }] }, null, [], NOW);
    const { merged } = mergeSyncState(local, remote);
    expect((merged.values.kk_tx as { amount: number }[])[0].amount).toBe(2);
  });

  it("トゥームストーンで削除されたレコードは消える", () => {
    const local = buildSyncState({ kk_tx: [{ id: "a", updatedAt: EARLIER }] }, null, [{ id: "a", deletedAt: LATER }], NOW);
    const remote = buildSyncState({ kk_tx: [{ id: "a", updatedAt: EARLIER }] }, null, [], NOW);
    const { merged } = mergeSyncState(local, remote);
    expect(merged.values.kk_tx).toEqual([]);
  });
});

describe("mergeSyncState 単一値", () => {
  it("新しい方の単一値を採用する（LWW）", () => {
    const local = { ...emptySyncState(), values: { kk_budget: { food: 100 } }, singletonMeta: { kk_budget: EARLIER } };
    const remote = { ...emptySyncState(), values: { kk_budget: { food: 200 } }, singletonMeta: { kk_budget: LATER } };
    const { merged } = mergeSyncState(local, remote);
    expect(merged.values.kk_budget).toEqual({ food: 200 });
  });

  it("base以降に両端末で変わり、中身が違えば conflict に載る", () => {
    const base = { ...emptySyncState(), singletonMeta: { kk_budget: EARLIER } };
    const local = { ...emptySyncState(), values: { kk_budget: { food: 100 } }, singletonMeta: { kk_budget: NOW } };
    const remote = { ...emptySyncState(), values: { kk_budget: { food: 200 } }, singletonMeta: { kk_budget: LATER } };
    const { conflicts } = mergeSyncState(local, remote, base);
    expect(conflicts).toContain("kk_budget");
  });

  it("片方しか変わっていなければ conflict にならない", () => {
    const base = { ...emptySyncState(), singletonMeta: { kk_budget: EARLIER } };
    const local = { ...emptySyncState(), values: { kk_budget: { food: 100 } }, singletonMeta: { kk_budget: EARLIER } };
    const remote = { ...emptySyncState(), values: { kk_budget: { food: 200 } }, singletonMeta: { kk_budget: LATER } };
    const { conflicts } = mergeSyncState(local, remote, base);
    expect(conflicts).not.toContain("kk_budget");
  });

  it("競合時は conflictDetails に両端末の値が載る", () => {
    const base = { ...emptySyncState(), singletonMeta: { kk_budget: EARLIER } };
    const local = { ...emptySyncState(), values: { kk_budget: { food: 100 } }, singletonMeta: { kk_budget: NOW } };
    const remote = { ...emptySyncState(), values: { kk_budget: { food: 200 } }, singletonMeta: { kk_budget: LATER } };
    const { conflictDetails } = mergeSyncState(local, remote, base);
    expect(conflictDetails).toEqual([{ key: "kk_budget", local: { food: 100 }, remote: { food: 200 } }]);
  });
});

describe("detectTombstones", () => {
  it("base に有ったが今は消えたレコードを墓標にする", () => {
    const base = buildSyncState({ kk_tx: [{ id: "a" }, { id: "b" }] }, null, [], EARLIER);
    const result = detectTombstones(base, { kk_tx: [{ id: "a" }] }, [], NOW);
    expect(result).toEqual([{ id: "b", deletedAt: NOW }]);
  });

  it("base が無ければ既存の墓標をそのまま返す", () => {
    const existing = [{ id: "x", deletedAt: EARLIER }];
    expect(detectTombstones(null, { kk_tx: [] }, existing, NOW)).toEqual(existing);
  });

  it("既に墓標があるidは二重に積まない", () => {
    const base = buildSyncState({ kk_tx: [{ id: "a" }] }, null, [], EARLIER);
    const existing = [{ id: "a", deletedAt: EARLIER }];
    const result = detectTombstones(base, { kk_tx: [] }, existing, NOW);
    expect(result).toHaveLength(1);
  });
});

describe("SYNC_KEYS", () => {
  it("配列11種・単一値3種を定義している", () => {
    expect(SYNC_KEYS.filter(k => k.kind === "array")).toHaveLength(11);
    expect(SYNC_KEYS.filter(k => k.kind === "singleton")).toHaveLength(3);
  });
});
