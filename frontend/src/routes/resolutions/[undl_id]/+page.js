import { api } from '$lib/api.js';

export async function load({ params, fetch }) {
  const resolution = await api(`/resolutions/${params.undl_id}`, null, fetch);
  return { resolution };
}
