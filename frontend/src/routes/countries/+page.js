import { api } from '$lib/api.js';

export async function load({ fetch }) {
  const countries = await api('/countries', null, fetch);
  return { countries };
}
