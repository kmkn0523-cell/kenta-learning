import { useState, useEffect, useCallback, useContext, useRef } from "react";
import CryptoKeyContext from "../contexts/CryptoKeyContext";
import { encryptValue, decryptValue, isEncrypted } from "../utils/crypto";

// ────────── 暗号化localStorageカスタムhook ──────────
// ブラウザの localStorage にデータを暗号化して保存する
// PasswordGate が用意した鍵束(current=新31万回 / legacy=旧10万回)を Context から受け取って暗号化／復号する
// スマホ・PCそれぞれのブラウザにデータが保存される

// 復号に失敗したことを画面側へ伝えるためのsessionStorageキー。
// App側がこれを見て「データを復号できませんでした」の警告バナーを出す。
export const DECRYPT_ERROR_FLAG = "kk_decrypt_error";

// T: 保存するデータの型（呼び出し元が決める）
// 戻り値: [現在値, 更新関数, 読み込み完了フラグ]
export function usePersist<T>(key: string, init: T): [T, (u: T | ((prev: T) => T)) => void, boolean] {
  // Context から AES-GCM 鍵束を受け取る（PasswordGate がログイン成功時にセットしてくれる）
  const keyRing = useContext(CryptoKeyContext);
  // このフックインスタンスごとに独立したキャッシュ（useRef でマウント単位で管理）
  // モジュールレベルの共有 mem を使うと、アンマウント後も値が残ってしまうバグがあった
  const memRef = useRef<T | undefined>(undefined);
  // 復号に失敗したフラグ。true の間は localStorage への書き込みを止めて、
  // 読めなかった暗号文を空データで上書き消失させないようにする（データ保護の要）。
  const decryptFailedRef = useRef(false);
  const [val, setVal] = useState<T>(init);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!keyRing) return; // 鍵が無い間は何もしない（PasswordGate が出てる時など）
    let alive = true;
    (async () => {
      try {
        const saved = localStorage.getItem(key);
        if (saved) {
          let parsed: T;
          if (isEncrypted(saved)) {
            // 暗号化済み → まず新鍵(current)で復号を試し、ダメなら旧鍵(legacy)で試す
            try {
              parsed = await decryptValue(keyRing.current, saved) as T;
            } catch (_currentError) {
              try {
                // 旧10万回の鍵で読めた → 中身は無事。新鍵で暗号化し直して段階移行する
                parsed = await decryptValue(keyRing.legacy, saved) as T;
                try {
                  const reEncrypted = await encryptValue(keyRing.current, parsed);
                  localStorage.setItem(key, reEncrypted);
                } catch (error) { console.warn("[usePersist] re-encrypt(migrate) failed", { key, error }); }
              } catch (error) {
                // 新鍵・旧鍵のどちらでも復号できない → データ消失を防ぐため上書きを禁止し、画面に警告を出す
                console.warn("[usePersist] decrypt failed (both keys)", { key, error });
                decryptFailedRef.current = true;
                try { sessionStorage.setItem(DECRYPT_ERROR_FLAG, "1"); } catch (_) { /* sessionStorage不可でも続行 */ }
                if (alive) setReady(true);
                return;
              }
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
              const encStored = await encryptValue(keyRing.current, parsed);
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
  }, [key, keyRing]);

  const set = useCallback((u: T | ((prev: T) => T)) => setVal(prev => {
    const next = typeof u === "function" ? (u as (prev: T) => T)(prev) : u;
    memRef.current = next;
    // 復号に失敗していたら localStorage には書かない（読めなかった暗号文を保全する）。画面表示だけ更新する。
    if (decryptFailedRef.current) {
      console.warn("[usePersist] skip save: decrypt previously failed", { key });
      return next;
    }
    // 暗号化（常に新31万回の鍵）してから localStorage に保存する（鍵がある時だけ）
    if (keyRing) {
      (async () => {
        try {
          const encStored = await encryptValue(keyRing.current, next);
          localStorage.setItem(key, encStored);
        } catch (error) { console.warn("[usePersist] save failed", { key, error }); }
      })();
    }
    return next;
  }), [key, keyRing]);

  return [val, set, ready];
}
