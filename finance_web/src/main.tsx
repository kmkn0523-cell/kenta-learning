import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// getElementById は null を返す可能性があるので ! で「必ずある」と TypeScript に伝える
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
