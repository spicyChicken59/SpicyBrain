import { createRoot } from "react-dom/client";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/instrument-sans";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./generated/design.css";
import "./styles.css";
import "./teaching.css";
import App from "./App";
import { store, StudyProvider } from "./ui";
void store.init();
window.addEventListener("beforeprint", () => {
  document
    .querySelectorAll<HTMLDetailsElement>(
      ".module-handbook details,.course-handbook details",
    )
    .forEach((d) => {
      if (!d.open) {
        d.dataset.printOpened = "true";
        d.open = true;
      }
    });
});
window.addEventListener("afterprint", () => {
  document
    .querySelectorAll<HTMLDetailsElement>("details[data-print-opened]")
    .forEach((d) => {
      d.open = false;
      delete d.dataset.printOpened;
    });
});
window.addEventListener("beforeunload", (event) => {
  const s = store.getSnapshot();
  if (s.status === "saving" || s.status === "unsaved") {
    event.preventDefault();
    event.returnValue = "";
  }
});
createRoot(document.getElementById("root")!).render(
  <StudyProvider>
    <App />
  </StudyProvider>,
);
