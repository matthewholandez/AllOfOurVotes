import { api } from '$lib/api.js';

const LIMIT = 25;

export async function load({ url, fetch }) {
  const body = url.searchParams.get('body') || '';
  const subject_id = url.searchParams.get('subject_id') || '';
  const from_date = url.searchParams.get('from') || '';
  const to_date = url.searchParams.get('to') || '';
  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10));
  const offset = (page - 1) * LIMIT;

  const [resolutions, subjects] = await Promise.all([
    api('/resolutions', { body, subject_id, from_date, to_date, limit: LIMIT, offset }, fetch),
    api('/subjects', null, fetch)
  ]);
  return { resolutions, subjects, filters: { body, subject_id, from_date, to_date }, page, limit: LIMIT };
}
