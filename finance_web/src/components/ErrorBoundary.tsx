// ────────── エラーバウンダリ ──────────
// Reactコンポーネントで予期しないエラーが発生したとき、
// 画面が真っ白になるのを防いで「再読み込み」画面を表示するセーフティネット

import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;  // エラーが発生したかどうかのフラグ
  error: Error | null; // 発生したエラーの内容（デバッグ用）
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  // 子コンポーネントでエラーが起きたときにReactが自動で呼び出す
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  // エラーの詳細をコンソールに記録する（開発時のデバッグ用）
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary] 予期しないエラーが発生しました:", error, info.componentStack);
  }

  // 「再読み込み」ボタンを押したときにページをリロードする
  handleReload() {
    window.location.reload();
  }

  render() {
    // エラーが起きていなければ通常通り子コンポーネントを描画
    if (!this.state.hasError) {
      return this.props.children;
    }

    // エラー発生時のフォールバック画面
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a0c",
        padding: 24,
      }}>
        <div style={{
          width: "100%",
          maxWidth: 360,
          textAlign: "center",
        }}>
          {/* エラーアイコン */}
          <div style={{ fontSize: 52, marginBottom: 16 }}>⚠️</div>

          {/* タイトル */}
          <div style={{
            fontSize: 18,
            fontWeight: 700,
            color: "#f5f5f7",
            marginBottom: 10,
          }}>
            表示中にエラーが発生しました
          </div>

          {/* 説明文 */}
          <div style={{
            fontSize: 13,
            color: "#9a9aa3",
            lineHeight: 1.7,
            marginBottom: 28,
          }}>
            予期しないエラーが起きました。<br />
            再読み込みすると復旧することがあります。<br />
            データは端末に保存されているので消えません。
          </div>

          {/* 再読み込みボタン */}
          <button
            onClick={this.handleReload}
            style={{
              width: "100%",
              padding: "14px 0",
              borderRadius: 12,
              border: "none",
              background: "#818cf8",
              color: "#0a0a0c",
              fontSize: 15,
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            再読み込みする
          </button>

          {/* エラー詳細（折りたたみ） */}
          {this.state.error && (
            <details style={{ marginTop: 20, textAlign: "left" }}>
              <summary style={{ fontSize: 12, color: "#5a5a63", cursor: "pointer" }}>
                エラー詳細（開発者向け）
              </summary>
              <pre style={{
                marginTop: 8,
                padding: 10,
                background: "rgba(255,255,255,0.04)",
                borderRadius: 8,
                fontSize: 12,
                color: "#f87171",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
              }}>
                {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      </div>
    );
  }
}
