import { api } from '$lib/api.js';

const LIMIT = 50;

export async function load({ params, url, fetch }) {
  const body = url.searchParams.get('body') || '';
  const vote = url.searchParams.get('vote') || '';
  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10));
  const offset = (page - 1) * LIMIT;
  const ms = params.ms_code.toUpperCase();

  const [country, votes] = await Promise.all([
    api(`/countries/${ms}`, null, fetch),
    api(`/countries/${ms}/votes`, { body, vote, limit: LIMIT, offset }, fetch)
  ]);
  return { country, votes, filters: { body, vote }, page, limit: LIMIT };
}
