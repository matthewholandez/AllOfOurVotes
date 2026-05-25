<script>
  import { goto } from '$app/navigation';
  import { page as pageStore } from '$app/stores';
  import { tallyText, outcomeLabel, fmtDate, fmtYear, VOTE_LABEL } from '$lib/api.js';

  let { data } = $props();
  let c = $derived(data.country);

  let body = $state(data.filters.body);
  let vote = $state(data.filters.vote);

  function apply() {
    const sp = new URLSearchParams();
    if (body) sp.set('body', body);
    if (vote) sp.set('vote', vote);
    goto(`/countries/${c.ms_code}` + (sp.toString() ? '?' + sp : ''));
  }

  function pageUrl(p) {
    const sp = new URLSearchParams($pageStore.url.searchParams);
    sp.set('page', String(p));
    return `/countries/${c.ms_code}?` + sp.toString();
  }

  // Tally the loaded page (the API gives us paged items only; show their split)
  let pageStats = $derived.by(() => {
    const s = { Y: 0, N: 0, A: 0, X: 0 };
    for (const v of data.votes.items) s[v.vote]++;
    const t = Math.max(1, data.votes.items.length);
    return {
      Y: Math.round((s.Y / t) * 100),
      N: Math.round((s.N / t) * 100),
      A: Math.round((s.A / t) * 100),
      X: Math.round((s.X / t) * 100)
    };
  });

  let total = $derived(data.votes.total);
  let pageCount = $derived(Math.max(1, Math.ceil(total / data.limit)));
  let pageNum = $derived(data.page);

  // Find the most-recent and earliest name in history
  let nameSpan = $derived.by(() => {
    if (!c.name_history?.length) return null;
    const sorted = [...c.name_history].sort((a, b) => a.valid_from.localeCompare(b.valid_from));
    return { first: sorted[0], last: sorted[sorted.length - 1] };
  });
</script>

<svelte:head>
  <title>{c.name ?? c.ms_code} — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <a href="/countries">Countries</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">{c.name ?? c.ms_code}</span>
    </div>

    <header class="country-hero">
      <div class="country-name">
        <h1>{c.name ?? c.ms_code}</h1>
        <span class="iso">{c.ms_code}{c.m49_code != null ? ' · M49 ' + c.m49_code : ''}</span>
      </div>
      <div class="meta" style="padding-bottom: 6px;">
        <span><span class="label">Votes recorded</span><br/><strong>{total.toLocaleString()}</strong></span>
        {#if nameSpan}
          <span><span class="label">First on record</span><br/><strong>{fmtYear(nameSpan.first.valid_from)}</strong></span>
        {/if}
      </div>
    </header>

    <div class="country-stats">
      <div class="country-stat">
        <div class="lbl">In favor</div>
        <div class="v" style="color: var(--for);">{pageStats.Y}%</div>
        <div class="sub">of this page</div>
      </div>
      <div class="country-stat">
        <div class="lbl">Against</div>
        <div class="v" style="color: var(--against);">{pageStats.N}%</div>
        <div class="sub">of this page</div>
      </div>
      <div class="country-stat">
        <div class="lbl">Abstained</div>
        <div class="v" style="color: var(--abstain);">{pageStats.A}%</div>
        <div class="sub">of this page</div>
      </div>
      <div class="country-stat">
        <div class="lbl">Did not vote</div>
        <div class="v" style="color: var(--fg-3);">{pageStats.X}%</div>
        <div class="sub">absent or non-voting</div>
      </div>
    </div>

    <div class="country-grid">
      <div>
        <div class="tabs" style="margin-top: 0;">
          <span class="tab current">Voting record</span>
        </div>

        <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;">
          <span class="overline" style="margin: 0;">Filter:</span>
          <select bind:value={body} on:change={apply} style="padding: 4px 8px; border: 1px solid var(--rule-soft); background: var(--bg-elev); color: var(--fg); font: inherit; font-size: 12px; border-radius: var(--r-1);">
            <option value="">Both bodies</option>
            <option value="GA">General Assembly</option>
            <option value="SC">Security Council</option>
          </select>
          <select bind:value={vote} on:change={apply} style="padding: 4px 8px; border: 1px solid var(--rule-soft); background: var(--bg-elev); color: var(--fg); font: inherit; font-size: 12px; border-radius: var(--r-1);">
            <option value="">Any vote</option>
            <option value="Y">Yes</option>
            <option value="N">No</option>
            <option value="A">Abstain</option>
            <option value="X">Non-voting</option>
          </select>
        </div>

        {#if data.votes.items.length === 0}
          <div class="empty">No votes match these filters.</div>
        {/if}
        {#each data.votes.items as v (v.undl_id)}
          <a class="country-vote-row" href="/resolutions/{v.undl_id}">
            <span class="date">{fmtDate(v.vote_date)}</span>
            <span>
              <div style="font-size: 14px; font-weight: 500; line-height: 1.35;">{v.title}</div>
              <div style="font-family: var(--mono); font-size: 11px; color: var(--fg-3); margin-top: 4px;">
                {v.resolution_code} · {v.body === 'GA' ? 'General Assembly' : 'Security Council'}
              </div>
            </span>
            <span class="tally-cell">
              {#if v.body === 'SC' && v.permanent_member && v.vote === 'N'}
                <span class="serif-italic" style="color: var(--against); font-size: 11px;">Vetoed</span>
              {:else}
                P{v.permanent_member ? '5' : ''}
              {/if}
            </span>
            <span class="their-vote {v.vote}">{VOTE_LABEL[v.vote]}</span>
          </a>
        {/each}

        <div class="pager">
          <span>Page {pageNum} of {pageCount.toLocaleString()} · {total.toLocaleString()} votes total</span>
          <div class="ctrls">
            {#if pageNum > 1}
              <a class="btn ghost sm" href={pageUrl(pageNum - 1)}>← Previous</a>
            {/if}
            {#if pageNum < pageCount}
              <a class="btn ghost sm" href={pageUrl(pageNum + 1)}>Next →</a>
            {/if}
          </div>
        </div>
      </div>

      <aside class="sidebar">
        <h3>About</h3>
        <div class="row"><span class="k">ISO code</span><span class="v mono">{c.ms_code}</span></div>
        {#if c.m49_code != null}<div class="row"><span class="k">M49 code</span><span class="v mono">{c.m49_code}</span></div>{/if}
        {#if c.name}<div class="row"><span class="k">Current name</span><span class="v">{c.name}</span></div>{/if}

        {#if c.name_history?.length > 1}
          <h3 style="margin-top: 28px;">Name history</h3>
          <ul style="list-style: none; padding: 0; margin: 0;">
            {#each [...c.name_history].sort((a, b) => b.valid_from.localeCompare(a.valid_from)) as h}
              <li style="padding: 8px 0; border-top: 1px solid var(--rule-hair); font-size: 13px;">
                <div style="font-weight: 500;">{h.name}</div>
                <div class="caption" style="font-family: var(--mono); font-size: 11px; letter-spacing: 0.04em;">
                  {fmtYear(h.valid_from)} – {h.valid_to ? fmtYear(h.valid_to) : 'present'}
                </div>
              </li>
            {/each}
          </ul>
        {/if}
      </aside>
    </div>
  </div>
</main>
