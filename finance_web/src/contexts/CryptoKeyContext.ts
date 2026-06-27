import { createContext } from "react";

// パスワードから派生したAES-GCMの鍵束（キーリング）を、アプリ全体から参照できるようにする箱。
// current = 新v2鍵(PBKDF2 31万回)。これから暗号化するときは必ずこちらを使う。
// legacy  = 旧v1鍵(PBKDF2 10万回)。過去に保存した暗号文を読むためだけに使う（段階移行用）。
// PasswordGate がログイン成功時に両方を派生してセットし、usePersist が読み取って暗号化・復号に使う。
export interface CryptoKeyRing {
  current: CryptoKey; // 新規暗号化に使う鍵（31万回）
  legacy: CryptoKey;  // 旧データ復号のフォールバック鍵（10万回）
}

const CryptoKeyContext = createContext<CryptoKeyRing | null>(null);

export default CryptoKeyContext;
