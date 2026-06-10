import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePersist } from "../../hooks/usePersist";

describe("usePersist mem isolation", () => {
  it("異なるキーのフックが互いに干渉しない", async () => {
    // フック A をマウント
    const { result: a } = renderHook(() => usePersist<string>("test_a", "initialA"));
    // フック B をマウント
    const { result: b } = renderHook(() => usePersist<string>("test_b", "initialB"));

    // A を更新
    act(() => {
      a.current[1]("updatedA");
    });

    // B の値が A に汚染されていないことを確認
    expect(a.current[0]).toBe("updatedA");
    expect(b.current[0]).toBe("initialB");
  });

  it("同じキーで再マウントしても前回の mem は残らない", async () => {
    const { result: first, unmount } = renderHook(() => usePersist<string>("test_c", "first"));
    // 最初のマウントで値を更新して mem に保存させる
    act(() => { first.current[1]("firstUpdated"); });
    unmount();

    // 別の初期値で再マウント — モジュールレベル mem が残っていると "firstUpdated" が返る
    const { result } = renderHook(() => usePersist<string>("test_c", "second"));
    // useRef ベースに直した後は init="second" が初期値になるはず
    expect(result.current[0]).toBe("second");
  });
});
