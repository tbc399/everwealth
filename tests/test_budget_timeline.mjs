import assert from 'node:assert/strict';
import test from 'node:test';
import { initBudgetTimeline } from '../everwealth/static/src/budget-timeline.js';

function fixture(selected = null) {
  const events = {};
  const buttons = [-1, 1].map(direction => ({
    dataset: { monthScroll: String(direction) },
    addEventListener(type, callback) { this[type] = callback; },
  }));
  const strip = {
    scrollLeft: 0, clientWidth: 200, scrollWidth: 600,
    querySelector: () => selected,
    addEventListener(type, callback) { events[type] = callback; },
    scrollBy(options) {
      this.behavior = options.behavior;
      this.scrollLeft = Math.max(0, Math.min(400, this.scrollLeft + options.left));
      events.scroll();
    },
  };
  const timeline = {
    querySelector: () => strip,
    querySelectorAll: () => buttons,
  };
  const root = { querySelectorAll: () => [timeline] };
  return { strip, buttons, root };
}

globalThis.ResizeObserver = class { observe() {} };
globalThis.matchMedia = () => ({ matches: false });

test('arrows scroll in both directions and disable at the ends', () => {
  const { root, strip, buttons: [left, right] } = fixture();
  initBudgetTimeline(root);
  assert.equal(left.disabled, true);
  assert.equal(right.disabled, false);
  right.click();
  assert.equal(strip.scrollLeft, 160);
  assert.equal(left.disabled, false);
  assert.equal(strip.behavior, 'smooth');
  right.click();
  right.click();
  assert.equal(strip.scrollLeft, 400);
  assert.equal(right.disabled, true);
  left.click();
  assert.equal(strip.scrollLeft, 240);
  assert.equal(right.disabled, false);
});

test('selected month is centered once, including when a partial is replaced', () => {
  const first = fixture({ offsetLeft: 300, offsetWidth: 80 });
  initBudgetTimeline(first.root);
  assert.equal(first.strip.scrollLeft, 240);
  first.strip.scrollLeft = 10;
  initBudgetTimeline(first.root);
  assert.equal(first.strip.scrollLeft, 10);
  const replacement = fixture({ offsetLeft: 350, offsetWidth: 80 });
  initBudgetTimeline(replacement.root);
  assert.equal(replacement.strip.scrollLeft, 290);
});

test('scroll controls honor reduced motion', () => {
  globalThis.matchMedia = () => ({ matches: true });
  const { root, strip, buttons } = fixture();
  initBudgetTimeline(root);
  buttons[1].click();
  assert.equal(strip.behavior, 'instant');
});
