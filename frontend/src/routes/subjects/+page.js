import { api } from '$lib/api.js';

export async function load({ fetch }) {
  const subjects = await api('/subjects', null, fetch);
  return { subjects };
}
