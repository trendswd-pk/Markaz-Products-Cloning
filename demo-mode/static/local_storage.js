/**
 * Browser localStorage helper for Demo Mode.
 * Keys are namespaced per demo user: markaz_demo_{username}
 */
export const STORAGE_NAMESPACE = 'markaz_demo';

export function storageKey(username) {
  return `${STORAGE_NAMESPACE}_${String(username || 'guest').replace(/[^a-zA-Z0-9_-]/g, '_')}`;
}

export function loadUserStore(username) {
  const raw = localStorage.getItem(storageKey(username));
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

export function saveUserStore(username, data) {
  localStorage.setItem(storageKey(username), JSON.stringify(data));
}

export function getItem(username, key, fallback = null) {
  const store = loadUserStore(username);
  return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : fallback;
}

export function setItem(username, key, value) {
  const store = loadUserStore(username);
  store[key] = value;
  saveUserStore(username, store);
}
