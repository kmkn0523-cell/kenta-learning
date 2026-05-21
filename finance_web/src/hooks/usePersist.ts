import { useState, useEffect, useCallback, useContext, useRef } from "react";
import CryptoKeyContext from "../contexts/CryptoKeyContext";
import { encryptValue, decryptValue, isEncrypted } from "../utils/crypto";

// ────────── 暗号化localStorageカスタムhook ──────────
// ブラウザの localStorage にデータを暗号化して保存する
// PasswordGate が用意した cryptoKey を Context から受け取って暗号化／復号する
// スマホ・PCそれぞれのブラウザにデータが保存される

// T: 保存するデータの型（呼び出し元が決める）
// 戻り値: [現在値, 更新関数, 読み込み完了フラグ]
export function usePersist<T>(key: string, init: T): [T, (u: T | ((prev: T) => T)) => void, boolean] {
  // Context から AES-GCM 鍵を受け取る（PasswordGate がログイン成功時にセットしてくれる）
  const cryptoKey = useContext(CryptoKeyContext);
  // このフックインスタンスごとに独立したキャッシュ（useRef でマウント単位で管理）
  // モジュールレベルの共有 mem を使うと、アンマウント後も値が残ってしまうバグがあった
  const memRef = useRef<T | undefined>(undefined);
  const [val, setVal] = useState<T>(init);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!cryptoKey) return; // 鍵が無い間は何もしない（PasswordGate が出てる時など）
    let alive = true;
    (async () => {
      try {
        const saved = localStorage.getItem(key);
        if (saved) {
          let parsed: T;
          if (isEncrypted(saved)) {
            // 暗号化済み → 復号
            try {
              parsed = await decryptValue(cryptoKey, saved) as T;
            } catch (error) {
              console.warn("[usePersist] decrypt failed", { key, error });
              if (alive) setReady(true);
              return;
            }
          } else {
            // 旧形式（平文JSON）→ パースして即座に暗号化して保存し直す（自動アップグレード）
            try {
              parsed = JSON.parse(saved) as T;
            } catch (error) {
              console.warn("[usePersist] JSON.parse failed", { key, error });
              if (alive) setReady(true);
              return;
            }
            try {
              const encStored = await encryptValue(cryptoKey, parsed);
              localStorage.setItem(key, encStored);
            } catch (error) { console.warn("[usePersist] re-encrypt failed", { key, error }); }
          }
          if (alive) {
            memRef.current = parsed;
            setVal(parsed);
          }
        }
      } catch (error) { console.warn("[usePersist] load failed", { key, error }); }
      if (alive) setReady(true);
    })();
    return () => { alive = false; };
  }, [key, cryptoKey]);

  const set = useCallback((u: T | ((prev: T) => T)) => setVal(prev => {
    const next = typeof u === "function" ? (u as (prev: T) => T)(prev) : u;
    memRef.current = next;
    // 暗号化してから localStorage に保存する（鍵がある時だけ）
    if (cryptoKey) {
      (async () => {
        try {
          const encStored = await encryptValue(cryptoKey, next);
          localStorage.setItem(key, encStored);
        } catch (error) { console.warn("[usePersist] save failed", { key, error }); }
      })();
    }
    return next;
  }), [key, cryptoKey]);

  return [val, set, ready];
}
