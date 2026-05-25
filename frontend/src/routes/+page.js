import { api } from '$lib/api.js';

export async function load({ fetch }) {
  const [resolutions, subjects] = await Promise.all([
    api('/resolutions', { limit: 8 }, fetch),
    api('/subjects', null, fetch)
  ]);
  return { resolutions, subjects };
}
