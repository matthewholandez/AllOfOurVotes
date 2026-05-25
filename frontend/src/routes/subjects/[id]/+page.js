import { api } from '$lib/api.js';
import { error } from '@sveltejs/kit';

const LIMIT = 25;

export async function load({ params, url, fetch }) {
  const id = parseInt(params.id, 10);
  if (Number.isNaN(id)) throw error(404, 'Topic not found');

  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10));
  const offset = (page - 1) * LIMIT;

  const [subjects, resolutions] = await Promise.all([
    api('/subjects', null, fetch),
    api('/resolutions', { subject_id: id, limit: LIMIT, offset }, fetch)
  ]);

  const subject = subjects.find((s) => s.id === id);
  if (!subject) throw error(404, 'Topic not found');

  return { subject, subjects, resolutions, page, limit: LIMIT };
}
