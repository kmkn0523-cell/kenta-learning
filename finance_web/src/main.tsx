import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";

// getElementById は null を返す可能性があるので ! で「必ずある」と TypeScript に伝える
// ErrorBoundary でラップすることで、予期しないエラーが発生しても画面が消えずにフォールバック画面を表示する
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>
);
