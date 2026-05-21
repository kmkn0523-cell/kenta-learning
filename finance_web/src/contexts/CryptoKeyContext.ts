import { createContext } from "react";

// パスワードから派生したAES-GCMの鍵を、アプリ全体から参照できるようにする箱
// PasswordGate がログイン成功時にセットし、usePersist が読み取って暗号化・復号に使う
const CryptoKeyContext = createContext<CryptoKey | null>(null);

export default CryptoKeyContext;
