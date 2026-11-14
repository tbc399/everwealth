import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const header = readFileSync(new URL('../everwealth/templates/header.html', import.meta.url), 'utf8');
const script = header.match(/<script>([\s\S]*?)<\/script>/)[1];

function applyTheme(stored, prefersDark = false, storageAvailable = true) {
  const root = { dataset: { lightTheme: 'jaxon', darkTheme: 'dark' } };
  const storage = new Map(stored ? [['theme', stored]] : []);
  vm.runInNewContext(script, {
    document: { documentElement: root },
    matchMedia: () => ({ matches: prefersDark }),
    localStorage: {
      getItem(key) {
        if (!storageAvailable) throw new Error('Storage unavailable');
        return storage.get(key);
      },
      setItem(key, value) {
        if (!storageAvailable) throw new Error('Storage unavailable');
        storage.set(key, value);
      },
    },
  });
  return { theme: root.dataset.theme, stored: storage.get('theme') };
}

test('saved light preferences migrate to the Jaxon theme', () => {
  for (const value of ['light', 'winter', 'corporate', 'jaxon']) {
    assert.deepEqual(applyTheme(value, true), { theme: 'jaxon', stored: 'jaxon' });
  }
});

test('saved dark preferences are preserved', () => {
  for (const value of ['dark', 'dim', 'sunset']) {
    assert.deepEqual(applyTheme(value), { theme: 'dark', stored: 'dark' });
  }
});

test('new visitors follow their system preference', () => {
  assert.equal(applyTheme(undefined).theme, 'jaxon');
  assert.equal(applyTheme(undefined, true).theme, 'dark');
  assert.equal(applyTheme('unknown').theme, 'jaxon');
});

test('unavailable local storage does not prevent rendering', () => {
  assert.equal(applyTheme(undefined, false, false).theme, 'jaxon');
  assert.equal(applyTheme(undefined, true, false).theme, 'dark');
});
