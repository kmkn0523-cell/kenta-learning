// ──────── 自動引落の実行管理フック ────────
// 毎日1回、ローン・キャッシング・銀行ローンの返済を自動で残高に反映する
// タブを閉じて戻ってきた時や日付が変わった後も正しく動くように設計されている
import { useEffect, useRef } from "react";
import { Loan } from "../types";

interface UseAutoPaymentArgs {
  // 消費者金融ローン・キャッシング・銀行ローンそれぞれの更新関数
  setLoans: (u: Loan[] | ((p: Loan[]) => Loan[])) => void;
  setCashFlow: (u: Loan[] | ((p: Loan[]) => Loan[])) => void;
  setBalance: (u: Loan[] | ((p: Loan[]) => Loan[])) => void;
  // 全ての usePersist が復号完了した時に true になるフラグ
  ready: boolean;
}

export function useAutoPayment(args: UseAutoPaymentArgs) {
  const { setLoans, setCashFlow, setBalance, ready } = args;
  // 「最後に自動引落をチェックした日付」を記憶しておく入れ物（YYYY-MM-DD の文字列）
  // 同じ日に何度も処理が走らないように見張り、日付が変わった時だけ再実行できるようにする
  const lastAutoRunDate = useRef<string | null>(null);
  useEffect(() => {
    // データの復号がまだ終わっていないなら何もしない
    if (!ready) return;
    // 実際の引落チェック処理。effect の中で関数を定義しているのは、毎回最新の日付で動かしたいから
    function runAutopay() {
      // ★毎回ここで新しく現在時刻を取り直す（タブを開いたまま日付跨ぎしても正しく動く）
      const now = new Date();
      const todayKey = now.getFullYear()+"-"+String(now.getMonth()+1).padStart(2,"0")+"-"+String(now.getDate()).padStart(2,"0");
      // すでに今日この処理を走らせていたらスキップ（連続実行や StrictMode の二重実行を防ぐ）
      if (lastAutoRunDate.current === todayKey) return;
      lastAutoRunDate.current = todayKey;
      // 関数の中で setArr に「前の状態 → 新しい状態」のコールバックを渡すと、必ず最新のローン配列が手に入る
      function applyAuto(setArr: (u: Loan[] | ((p: Loan[]) => Loan[])) => void) {
        setArr(prev => {
          let changed = false;
          const updated = prev.map(loan => {
            // 自動モードがOFFのローンはスキップ
            if (!loan.autoMode) return loan;
            if (!loan.payDay || loan.payDay === "未設定") return loan;
            const dayNum = parseInt(loan.payDay);
            if (isNaN(dayNum)) return loan;
            let lastPaid = loan.lastAutoPaid;
            if (!lastPaid) {
              // 初回処理：前月の1日を仮の「最後に払った月」にしておくと、次のループで先月分から順に処理が走る
              const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
              lastPaid = d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0");
            }
            let [ly, lm] = lastPaid.split("-").map(Number);
            let remaining = loan.remaining;
            let newLastPaid = lastPaid;
            while (true) {
              lm++; if (lm > 12) { lm = 1; ly++; }
              // 今月を超えたらループを抜ける
              if (ly > now.getFullYear() || (ly === now.getFullYear() && lm > now.getMonth()+1)) break;
              // その月の最終日（30日や31日など）を取得し、引落日が月末を超えないように補正する
              const daysInMonth = new Date(ly, lm, 0).getDate();
              const actualDay = Math.min(dayNum, daysInMonth);
              const payDate = new Date(ly, lm-1, actualDay);
              if (now >= payDate && remaining > 0) {
                remaining = Math.max(0, remaining - loan.monthly);
                newLastPaid = ly + "-" + String(lm).padStart(2,"0");
                changed = true;
              }
            }
            return (newLastPaid !== loan.lastAutoPaid || remaining !== loan.remaining)
              ? { ...loan, remaining, lastAutoPaid: newLastPaid }
              : loan;
          });
          // 変更が無ければ元の配列をそのまま返す（無駄な再レンダリングを防ぐ）
          return changed ? updated : prev;
        });
      }
      applyAuto(setLoans);
      applyAuto(setCashFlow);
      applyAuto(setBalance);
    }
    // 起動時に1回実行
    runAutopay();
    // タブを再表示した時にも実行（日付跨ぎ対応：例えば前日23:50に開いて翌日午前に戻ってきたケース）
    function onVisible(){ if(document.visibilityState==="visible") runAutopay(); }
    document.addEventListener("visibilitychange", onVisible);
    // window がフォーカスされた時も再チェック（visibilitychange を発火しないブラウザ向けの保険）
    window.addEventListener("focus", runAutopay);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", runAutopay);
    };
  }, [ready, setLoans, setCashFlow, setBalance]);
}
