// Thin wrapper around the FastAPI backend.
// During dev, requests go through Vite's /api proxy → http://localhost:8000.
// In production, set PUBLIC_API_BASE in the environment.

import { browser } from '$app/environment';

const PUBLIC_API_BASE = browser ? '' : ''; // SSR also goes through /api (relative)
const BASE = '/api';

/**
 * @param {string} path
 * @param {URLSearchParams | Record<string, any>} [params]
 * @param {typeof fetch} [fetchFn]
 */
export async function api(path, params, fetchFn = fetch) {
  let url = BASE + path;
  if (params) {
    const sp = params instanceof URLSearchParams ? params : new URLSearchParams();
    if (!(params instanceof URLSearchParams)) {
      for (const [k, v] of Object.entries(params)) {
        if (v === undefined || v === null || v === '') continue;
        sp.set(k, String(v));
      }
    }
    const qs = sp.toString();
    if (qs) url += '?' + qs;
  }
  const res = await fetchFn(url, { headers: { accept: 'application/json' } });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${text || url}`);
  }
  return res.json();
}

export const VOTE_LABEL = { Y: 'Yes', N: 'No', A: 'Abstain', X: 'Non-voting' };

/**
 * @param {{ total_yes: number|null, total_no: number|null, total_abstentions: number|null, total_non_voting: number|null }} r
 */
export function tallyText(r) {
  const y = r.total_yes ?? 0;
  const n = r.total_no ?? 0;
  const a = r.total_abstentions ?? 0;
  return `${y}–${n}–${a}`;
}

/**
 * @param {{ total_yes: number|null, total_no: number|null }} r
 */
export function outcomeLabel(r) {
  const y = r.total_yes ?? 0;
  const n = r.total_no ?? 0;
  if (y > n) return 'Adopted';
  if (n > y) return 'Rejected';
  return 'Tied';
}

/**
 * Format an ISO date as e.g. "27 Oct 1983" — terse, sentence case style.
 * @param {string|null|undefined} iso
 */
export function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso + 'T00:00:00Z');
  if (Number.isNaN(d.getTime())) return iso;
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${d.getUTCDate()} ${months[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/**
 * @param {string|null|undefined} iso
 */
export function fmtYear(iso) {
  if (!iso) return '—';
  return iso.slice(0, 4);
}
