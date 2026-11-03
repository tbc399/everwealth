// Delegate events so the import dialog also works when inserted by HTMX.
const responseError = async (response) => {
  try {
    const { detail } = await response.json();
    if (typeof detail === "string") return detail;
  } catch {}
  return "The file could not be processed. Please try again.";
};

document.addEventListener("change", async (event) => {
  if (!event.target.matches("[data-upload-file]")) return;
  const input = event.target;
  const form = input.closest("[data-transaction-upload]");
  const mapping = form.querySelector("[data-upload-mapping]");
  const status = form.querySelector("[data-upload-status]");
  const error = form.querySelector("[data-upload-error]");
  const submit = form.querySelector('[type="submit"]');
  // A new selection invalidates any in-flight header request and old mappings.
  form.headerRequest?.abort();
  const controller = new AbortController();
  form.headerRequest = controller;
  mapping.hidden = true;
  mapping.disabled = true;
  submit.disabled = true;
  error.hidden = true;
  const file = input.files[0];
  status.textContent = file ? "Reading column headers…" : "Choose a CSV file to map its columns.";
  if (!file) return;
  try {
    const body = new FormData();
    body.append("file", file);
    const response = await fetch("/transactions/upload/headers", {
      method: "POST", body, signal: controller.signal,
    });
    if (response.redirected) { location.assign(response.url); return; }
    if (!response.ok) throw new Error(await responseError(response));
    const data = await response.json();
    if (controller.signal.aborted) return;
    mapping.querySelectorAll("[data-upload-column]").forEach((select) => {
      const field = select.dataset.uploadColumn;
      select.replaceChildren(new Option(field === "direction" ? "Use signed amounts" : "Select a column", ""));
      data.headers.forEach((header) => select.add(new Option(header, header)));
      select.value = data.mapping[field] || "";
    });
    mapping.hidden = false;
    mapping.disabled = false;
    submit.disabled = false;
    status.textContent = "Review the suggested mappings before importing.";
  } catch (failure) {
    if (controller.signal.aborted) return;
    status.textContent = "Choose a CSV file to map its columns.";
    error.textContent = failure.message;
    error.hidden = false;
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-transaction-upload]");
  if (!form) return;
  event.preventDefault();
  if (form.dataset.importing) return;
  const submit = form.querySelector('[type="submit"]');
  const error = form.querySelector("[data-upload-error]");
  const status = form.querySelector("[data-upload-status]");
  error.hidden = true;
  const body = new FormData(form);
  form.dataset.importing = "true";
  submit.disabled = true;
  status.textContent = "Importing transactions…";
  try {
    const response = await fetch(form.action, { method: "POST", body });
    if (response.redirected) { location.assign(response.url); return; }
    if (!response.ok) throw new Error(await responseError(response));
    location.assign("/transactions");
  } catch (failure) {
    error.textContent = failure.message;
    error.hidden = false;
    status.textContent = "Review your mappings and try again.";
    submit.disabled = false;
    delete form.dataset.importing;
  }
});
