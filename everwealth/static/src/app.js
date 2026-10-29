import {
  createIcons, ArrowLeft, ArrowLeftRight, ArrowRight,
  Check, ChevronLeft, ChevronRight, Download, FileSpreadsheet,
  Landmark, LayoutDashboard, Link, LogOut, Mail, Menu, Moon, Pencil, Plus,
  Search, Settings, ShieldCheck, Trash2, Unplug, Wallet, X,
} from "lucide";

const icons = {
  ArrowLeft, ArrowLeftRight, ArrowRight, Check,
  ChevronLeft, ChevronRight, Download, FileSpreadsheet,
  Landmark, LayoutDashboard, Link, LogOut, Mail, Menu, Moon, Pencil, Plus,
  Search, Settings, ShieldCheck, Trash2, Unplug, Wallet, X,
};
const media = matchMedia("(prefers-color-scheme: dark)");
const { lightTheme, darkTheme } = document.documentElement.dataset;
const storedTheme = () => {
  try { return localStorage.getItem("theme"); } catch { return null; }
};
const syncTheme = () => {
  document.querySelectorAll("[data-theme-toggle]").forEach((control) => {
    control.checked = document.documentElement.dataset.theme === darkTheme;
  });
};
const syncNavigation = () => {
  const path = location.pathname;
  const active = path.startsWith("/categories") ? "budgets"
    : path.startsWith("/settings") ? "settings" : path.split("/")[1] || "dashboard";
  document.querySelectorAll("[data-nav]").forEach((link) => {
    const selected = link.dataset.nav === active;
    link.classList.toggle("menu-active", selected);
    if (selected) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
};
const refresh = () => {
  createIcons({ icons });
  syncTheme();
  syncNavigation();
  const heading = document.querySelector("#main-content h1");
  if (heading) document.title = heading.textContent.trim() + " | Everwealth";
  document.querySelectorAll("dialog[data-modal]:not([open])").forEach((dialog) => {
    dialog.addEventListener("close", () => dialog.remove(), { once: true });
    dialog.showModal();
  });
};

document.addEventListener("change", (event) => {
  if (!event.target.matches("[data-theme-toggle]")) return;
  const theme = event.target.checked ? darkTheme : lightTheme;
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("theme", theme); } catch {}
  syncTheme();
});
media.addEventListener("change", () => {
  if ([lightTheme, darkTheme].includes(storedTheme())) return;
  document.documentElement.dataset.theme = media.matches ? darkTheme : lightTheme;
  syncTheme();
});
document.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-modal]")) event.target.closest("dialog")?.close();
  if (event.target.closest("[data-dismiss-error]")) document.getElementById("request-error")?.classList.add("hidden");
  if (event.target.closest("[data-nav]")) document.getElementById("navigation-drawer").checked = false;
});
document.addEventListener("keydown", (event) => {
  const label = event.target.closest('label[for="navigation-drawer"][role="button"]');
  if (label && ["Enter", " "].includes(event.key)) {
    event.preventDefault();
    document.getElementById("navigation-drawer").checked = true;
  }
});
document.body.addEventListener("htmx:afterSwap", refresh);
document.body.addEventListener("htmx:pushedIntoHistory", syncNavigation);
document.body.addEventListener("htmx:historyRestore", refresh);
document.body.addEventListener("htmx:beforeRequest", (event) => {
  const opener = event.detail.elt.closest("[data-edit-transaction]");
  if (!opener) return;
  document.querySelectorAll("[data-transaction-editor]").forEach((row) => {
    if (row.id === opener.closest("tr").id) return;
    window.htmx.ajax("GET", "/transactions/" + row.dataset.transactionEditor + "/row", { target: row, swap: "outerHTML" });
  });
});
const showError = (message) => {
  const toast = document.getElementById("request-error");
  if (!toast) return;
  toast.querySelector("[data-error-message]").textContent = message;
  toast.classList.remove("hidden");
};
document.body.addEventListener("htmx:responseError", (event) => {
  let message = "The request could not be completed. Please try again.";
  try {
    const detail = JSON.parse(event.detail.xhr.responseText).detail;
    if (typeof detail === "string") message = detail;
  } catch {}
  showError(message);
});
document.body.addEventListener("htmx:sendError", () => showError("Unable to connect. Please try again."));

let plaidLoader;
const loadPlaid = () => plaidLoader ||= new Promise((resolve, reject) => {
  if (window.Plaid) return resolve();
  const script = document.createElement("script");
  script.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
  script.onload = resolve;
  script.onerror = () => { plaidLoader = null; reject(new Error("Unable to load Plaid.")); };
  document.head.append(script);
});
const post = async (url, payload) => {
  const response = await fetch(url, {
    method: "POST",
    ...(payload && { headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  });
  if (!response.ok) throw new Error("Unable to connect your account. Please try again.");
  return response;
};
document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-connect-account]");
  if (!button) return;
  button.disabled = true;
  try {
    await loadPlaid();
    const data = await (await post("/accounts/create-link")).json();
    const handler = window.Plaid.create({
      token: data.link_token,
      onSuccess: async (publicToken) => {
        try {
          await post("/accounts/exchange-token", { public_token: publicToken });
          window.htmx.ajax("GET", "/accounts/partial", { target: "#main-content" });
        } catch (error) { showError(error.message); }
      },
      onExit: () => handler.destroy(),
    });
    handler.open();
  } catch (error) { showError(error.message); }
  finally { button.disabled = false; }
});

document.querySelectorAll("[data-otp]").forEach((form) => {
  const inputs = [...form.querySelectorAll("[inputmode=numeric]")];
  form.addEventListener("input", (event) => {
    const input = event.target;
    const index = inputs.indexOf(input);
    if (index < 0) return;
    const digits = input.value.replace(/\D/g, "");
    if (digits.length > 1) {
      digits.slice(0, inputs.length - index).split("").forEach((digit, offset) => { inputs[index + offset].value = digit; });
      inputs[Math.min(index + digits.length, inputs.length - 1)].focus();
    } else {
      input.value = digits;
      if (digits) inputs[index + 1]?.focus();
    }
  });
  form.addEventListener("keydown", (event) => {
    const index = inputs.indexOf(event.target);
    if (event.key === "Backspace" && !event.target.value) inputs[index - 1]?.focus();
  });
});

refresh();
