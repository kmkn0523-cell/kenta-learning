// ────────── アプリ全体で使うデータ型の定義 ──────────
// TypeScript にデータの「形」を教えるためのファイル

// 変動支出1件の形
export interface Tx {
  id: string;
  date: string;        // "YYYY-MM-DD" 形式
  category: string;
  amount: number;
  memo: string;
  accountId?: string;  // 紐づく口座ID（任意）
}

// 固定費1件の形
export interface FixedExpense {
  id: string;
  name: string;
  category: string;
  amount: number;
  payDay: string;       // "1日" 〜 "31日" または "未設定"
  lastAutoPaid?: string; // 最後に自動引落した日付
  active?: boolean;     // false にすると一時停止
  autoTrack?: boolean;  // true: 毎月変動支出として transactions に自動追加する
  lastAutoAdded?: string; // 自動追加した最後の月 "YYYY-MM"（重複防止に使う）
}

// ローン1件の形
export interface Loan {
  id: string;
  name: string;
  rate: number;       // 金利（%）
  remaining: number;  // 残債（円）
  monthly: number;    // 月返済額（円）
  principal: number;  // 借入元本（円）
  payDay: string;
  lastAutoPaid?: string;
  autoMode?: boolean;
}

// 収入1件の形
export interface Income {
  id: string;
  date: string;
  category: string;
  amount: number;
  memo: string;
  accountId?: string;  // 紐づく口座ID（任意）
}

// 口座残高1件の形
export interface Account {
  id: string;
  name: string;
  balance: number;
  color?: string;  // 口座を区別するためのカラーラベル（例: "#22c55e"）
}

// 口座間振替1件の形（例：財布→銀行 に2000円移動）
export interface Transfer {
  id: string;
  date: string;           // "YYYY-MM-DD" 形式
  fromAccountId: string;  // 振替元の口座ID
  toAccountId: string;    // 振替先の口座ID
  amount: number;         // 金額（円）
  memo?: string;          // 任意のメモ
}

// カテゴリ別予算の形（{食費: 30000, ...} など）
export type Budget = Record<string, number>;

// カテゴリ1件の形（名前・絵文字・表示順を持つ）
export interface CategoryItem {
  id: string;      // 一意なID
  name: string;    // カテゴリ名（例："食費"）
  icon: string;    // 絵文字（例："🍽️"）
  order: number;   // 表示順（数字が小さいほど上に表示）
}

// アプリ全体のカテゴリ設定（変動費・固定費・収入）
export interface CategoryConfig {
  expense: CategoryItem[];       // 変動費カテゴリ一覧
  fixedExpense: CategoryItem[];  // 固定費カテゴリ一覧
  income: CategoryItem[];        // 収入カテゴリ一覧
}

// 目標貯金1件の形（「2026年末までに100万円貯める」のような目標を表す）
// 現在貯金は口座残高合計を使う。startAmount は目標作成時点の貯金額をスナップショットとして保存し、
// 「目標設定後にどれだけ増えたか」の進捗計算に使う
export interface SavingGoal {
  id: string;
  name: string;          // 目標名（例: "2026年末までに100万円"）
  targetAmount: number;  // 目標金額（円）
  startAmount: number;   // 目標設定時の貯金額（達成率計算のベースライン）
  deadline: string;      // 達成期限 "YYYY-MM-DD"
  createdAt: string;     // 作成日 "YYYY-MM-DD"
}

// 定期収入1件の形（給与・副業など毎月一定額が入る収入を登録する）
export interface RecurringIncome {
  id: string;
  name: string;           // 収入名（例: "給与", "副業"）
  category: string;       // 収入カテゴリ
  amount: number;         // 金額（円）
  payDay: string;         // 振込日（"1日" 〜 "31日" または "未設定"）
  lastAutoAdded?: string; // 最後に自動追加した月 "YYYY-MM"（重複防止に使う）
  active?: boolean;       // false にすると自動追加を一時停止
}

// 繰り返し支出1件の形（毎月一定額が出ていく変動費を自動追加するための設定）
// 例：「月サブスク Netflix 1490円 毎月1日」
export interface RecurringExpense {
  id: string;
  name: string;            // 支出名（例: "Netflix", "ジム会費"）
  category: string;        // 変動費カテゴリ
  amount: number;          // 金額（円）
  payDay: string;          // 引落日（"1日" 〜 "31日" または "未設定"）
  lastAutoAdded?: string;  // 最後に自動追加した月 "YYYY-MM"（重複防止に使う）
  active?: boolean;        // false にすると自動追加を一時停止
}

// トースト通知の形
export interface ToastData {
  msg: string;
  type?: "success" | "error" | "info";
}

// 削除確認ダイアログの形
export interface DlgData {
  title: string;
  msg?: string;
  onOk: () => void;
}
