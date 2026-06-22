// ────────── クラウド同期 設定セクション ──────────
// 設計書: docs/finance_web_sync_design_v2.md §6。
// 設定画面に置く「☁️ クラウド同期」カード。
//  ・未設定: 「同期を始める」→ 復元キー(RK)を生成して1回だけ表示し保管を確認させる
//  ・別端末: 「復元キーで復元」→ RK入力して同期に参加
//  ・有効中: 状態・最終同期日時・「今すぐ同期」「同期を解除」
import { useState, CSSProperties } from "react";
import {
  STYLE_CARD,
  STYLE_BUTTON_PRIMARY,
  STYLE_BUTTON_OUTLINE,
  COLOR_TEXT_PRIMARY,
  COLOR_TEXT_SECONDARY,
  COLOR_ACCENT,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "../utils/styles";
import { generateRecoveryKey } from "../utils/crypto";
import type { SyncStatus } from "../hooks/useCloudSync";

const STYLE_LABEL: CSSProperties = { fontSize: 13, color: COLOR_TEXT_SECONDARY, marginBottom: 6 };
const STYLE_RK_BOX: CSSProperties = {
  fontFamily: "monospace",
  fontSize: 16,
  letterSpacing: 1,
  background: "rgba(255,255,255,0.06)",
  border: `1px solid ${COLOR_ACCENT}`,
  borderRadius: 10,
  padding: "12px 14px",
  color: COLOR_TEXT_PRIMARY,
  wordBreak: "break-all",
  marginBottom: 10,
};
const STYLE_INPUT: CSSProperties = {
  width: "100%",
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 10,
  color: COLOR_TEXT_PRIMARY,
  fontSize: 14,
  padding: "10px 12px",
  fontFamily: "monospace",
  marginBottom: 10,
};

// 状態に応じた表示文言と色
function statusLabel(status: SyncStatus): { text: string; color: string } {
  switch (status) {
    case "off": return { text: "オフ", color: COLOR_TEXT_SECONDARY };
    case "locked": return { text: "ロック中（パスワード入力で再開）", color: COLOR_ACCENT };
    case "idle": return { text: "同期中（待機）", color: COLOR_POSITIVE };
    case "syncing": return { text: "同期しています…", color: COLOR_ACCENT };
    case "conflict": return { text: "競合あり（要確認）", color: COLOR_NEGATIVE };
    case "error": return { text: "エラー", color: COLOR_NEGATIVE };
  }
}

interface CloudSyncSectionProps {
  status: SyncStatus;
  lastSyncedAt: string | null;
  // RK文字列＋この端末用パスワードを渡して同期に参加する（生成直後・復元の両方で使う）
  onActivate: (recoveryKey: string, password: string) => Promise<void>;
  // 保存済みRKをパスワードで解錠して再開する（リロード後）。成功でtrue
  onUnlock: (password: string) => Promise<boolean>;
  onDeactivate: () => void;
  onSyncNow: () => void;
}

export default function CloudSyncSection(props: CloudSyncSectionProps) {
  const { status, lastSyncedAt, onActivate, onUnlock, onDeactivate, onSyncNow } = props;
  // 画面のモード: "view"=状態表示 / "show-rk"=生成したRK表示 / "restore"=RK入力
  const [mode, setMode] = useState<"view" | "show-rk" | "restore">("view");
  const [generatedRk, setGeneratedRk] = useState("");
  const [rkSaved, setRkSaved] = useState(false);   // 「保管した」チェック
  const [restoreInput, setRestoreInput] = useState("");
  const [password, setPassword] = useState("");    // この端末用パスワード（RKを包む鍵）
  const [unlockInput, setUnlockInput] = useState(""); // ロック解除用パスワード入力
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const sl = statusLabel(status);
  const isOn = status !== "off";
  const isLocked = status === "locked";

  // 新しいRKを生成して表示する
  function startNew() {
    setError("");
    setGeneratedRk(generateRecoveryKey().display);
    setRkSaved(false);
    setMode("show-rk");
  }

  // 生成したRKで同期を開始する（パスワードでRKを包んで保存）
  async function confirmNew() {
    setBusy(true);
    setError("");
    try {
      await onActivate(generatedRk, password);
      setMode("view");
      setGeneratedRk("");
      setPassword("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "同期の開始に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  // 入力したRKで別端末から復元する（パスワードでRKを包んで保存）
  async function confirmRestore() {
    setBusy(true);
    setError("");
    try {
      await onActivate(restoreInput.trim(), password);
      setMode("view");
      setRestoreInput("");
      setPassword("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "復元に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  // 保存済みRKをパスワードで解錠して同期を再開する
  async function confirmUnlock() {
    setBusy(true);
    setError("");
    try {
      const ok = await onUnlock(unlockInput);
      if (!ok) { setError("パスワードが違います"); return; }
      setUnlockInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "解錠に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={{ ...STYLE_CARD, marginTop: 16 }}>
      <h3 style={{ fontSize: 15, color: COLOR_TEXT_PRIMARY, margin: "0 0 4px" }}>☁️ クラウド同期</h3>
      <p style={{ fontSize: 12, color: COLOR_TEXT_SECONDARY, margin: "0 0 14px" }}>
        スマホとPCなど複数の端末で家計データを同期します。中身は暗号化され、サーバからは読めません。
      </p>

      {/* 状態表示モード */}
      {mode === "view" && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={STYLE_LABEL}>状態</span>
            <span style={{ fontSize: 13, color: sl.color, fontWeight: 600 }}>{sl.text}</span>
          </div>
          {isOn && lastSyncedAt && (
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={STYLE_LABEL}>最終同期</span>
              <span style={{ fontSize: 13, color: COLOR_TEXT_PRIMARY }}>
                {new Date(lastSyncedAt).toLocaleString("ja-JP")}
              </span>
            </div>
          )}

          {isLocked ? (
            // リロード後：保存済みRKをパスワードで解錠して再開
            <>
              <div style={STYLE_LABEL}>この端末のパスワードを入力して同期を再開</div>
              <input
                style={STYLE_INPUT}
                type="password"
                value={unlockInput}
                onChange={e => setUnlockInput(e.target.value)}
                placeholder="パスワード"
                autoComplete="current-password"
                onKeyDown={e => { if (e.key === "Enter" && unlockInput && !busy) void confirmUnlock(); }}
              />
              {error && <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: "0 0 10px" }}>{error}</p>}
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="button"
                  style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, opacity: unlockInput && !busy ? 1 : 0.5 }}
                  disabled={!unlockInput || busy}
                  onClick={confirmUnlock}
                >
                  {busy ? "解錠しています…" : "同期を再開する"}
                </button>
                <button type="button" style={STYLE_BUTTON_OUTLINE} disabled={busy} onClick={onDeactivate}>
                  解除
                </button>
              </div>
            </>
          ) : !isOn ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <button type="button" style={STYLE_BUTTON_PRIMARY} onClick={startNew}>
                同期を始める（新しい復元キーを作る）
              </button>
              <button type="button" style={STYLE_BUTTON_OUTLINE} onClick={() => { setError(""); setMode("restore"); }}>
                復元キーで別端末から復元
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" style={{ ...STYLE_BUTTON_PRIMARY, flex: 1 }} onClick={onSyncNow}>
                今すぐ同期
              </button>
              <button type="button" style={STYLE_BUTTON_OUTLINE} onClick={onDeactivate}>
                同期を解除
              </button>
            </div>
          )}
        </>
      )}

      {/* 生成したRKを1回だけ表示するモード */}
      {mode === "show-rk" && (
        <>
          <div style={STYLE_LABEL}>あなたの復元キー（このキーが無いと別端末で復元できません）</div>
          <div style={STYLE_RK_BOX}>{generatedRk}</div>
          <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: "0 0 10px" }}>
            ⚠️ このキーは二度と表示されません。パスワード管理アプリやメモに必ず保管してください。
            キーとパスワードを両方失うとデータは復元できません。
          </p>
          <button
            type="button"
            style={{ ...STYLE_BUTTON_OUTLINE, width: "100%", marginBottom: 10 }}
            onClick={() => { void navigator.clipboard?.writeText(generatedRk); }}
          >
            📋 コピーする
          </button>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: COLOR_TEXT_PRIMARY, marginBottom: 12 }}>
            <input type="checkbox" checked={rkSaved} onChange={e => setRkSaved(e.target.checked)} />
            復元キーを安全な場所に保管しました
          </label>
          <div style={STYLE_LABEL}>この端末用のパスワード（次回起動時の再開に使う・4文字以上）</div>
          <input
            style={STYLE_INPUT}
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="パスワード"
            autoComplete="new-password"
          />
          {error && <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: "0 0 10px" }}>{error}</p>}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, opacity: rkSaved && password.length >= 4 && !busy ? 1 : 0.5 }}
              disabled={!rkSaved || password.length < 4 || busy}
              onClick={confirmNew}
            >
              {busy ? "開始しています…" : "この端末で同期を開始"}
            </button>
            <button type="button" style={STYLE_BUTTON_OUTLINE} disabled={busy} onClick={() => setMode("view")}>
              やめる
            </button>
          </div>
        </>
      )}

      {/* RK入力で復元するモード */}
      {mode === "restore" && (
        <>
          <div style={STYLE_LABEL}>復元キーを入力してください</div>
          <input
            style={STYLE_INPUT}
            value={restoreInput}
            onChange={e => setRestoreInput(e.target.value)}
            placeholder="XXXX-XXXX-XXXX-..."
            autoComplete="off"
          />
          <div style={STYLE_LABEL}>この端末用のパスワード（次回起動時の再開に使う・4文字以上）</div>
          <input
            style={STYLE_INPUT}
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="パスワード"
            autoComplete="new-password"
          />
          {error && <p style={{ fontSize: 12, color: COLOR_NEGATIVE, margin: "0 0 10px" }}>{error}</p>}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              style={{ ...STYLE_BUTTON_PRIMARY, flex: 1, opacity: restoreInput.trim() && password.length >= 4 && !busy ? 1 : 0.5 }}
              disabled={!restoreInput.trim() || password.length < 4 || busy}
              onClick={confirmRestore}
            >
              {busy ? "復元しています…" : "復元する"}
            </button>
            <button type="button" style={STYLE_BUTTON_OUTLINE} disabled={busy} onClick={() => setMode("view")}>
              やめる
            </button>
          </div>
        </>
      )}
    </section>
  );
}
