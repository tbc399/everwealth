const initialized = new WeakSet();

export function initBudgetTimeline(root = document) {
  root.querySelectorAll("[data-month-timeline]").forEach((timeline) => {
    if (initialized.has(timeline)) return;
    initialized.add(timeline);
    const strip = timeline.querySelector("[data-month-strip]");
    const buttons = timeline.querySelectorAll("[data-month-scroll]");
    const update = () => {
      buttons.forEach((button) => {
        button.disabled = Number(button.dataset.monthScroll) < 0
          ? strip.scrollLeft <= 1
          : strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 1;
      });
    };
    buttons.forEach((button) => button.addEventListener("click", () => {
      strip.scrollBy({
        left: Number(button.dataset.monthScroll) * strip.clientWidth * 0.8,
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
      });
    }));
    strip.addEventListener("scroll", update, { passive: true });
    const selected = strip.querySelector('[aria-current="date"]');
    if (selected) strip.scrollLeft = selected.offsetLeft - (strip.clientWidth - selected.offsetWidth) / 2;
    update();
    // Observe this strip only; removed partials should not leave window listeners behind.
    const observer = new ResizeObserver(update);
    observer.observe(strip);
  });
}
