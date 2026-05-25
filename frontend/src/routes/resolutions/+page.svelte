<script>
  import { goto } from '$app/navigation';
  import { page as pageStore } from '$app/stores';
  import { tallyText, outcomeLabel, fmtDate } from '$lib/api.js';

  let { data } = $props();

  let body = $state(data.filters.body);
  let subject_id = $state(data.filters.subject_id);
  let from_date = $state(data.filters.from_date);
  let to_date = $state(data.filters.to_date);

  function apply() {
    const sp = new URLSearchParams();
    if (body) sp.set('body', body);
    if (subject_id) sp.set('subject_id', subject_id);
    if (from_date) sp.set('from', from_date);
    if (to_date) sp.set('to', to_date);
    goto('/resolutions' + (sp.toString() ? '?' + sp : ''));
  }

  function reset() {
    body = ''; subject_id = ''; from_date = ''; to_date = '';
    goto('/resolutions');
  }

  function pageUrl(p) {
    const sp = new URLSearchParams($pageStore.url.searchParams);
    sp.set('page', String(p));
    return '/resolutions?' + sp.toString();
  }

  let total = $derived(data.resolutions.total);
  let pageCount = $derived(Math.max(1, Math.ceil(total / data.limit)));
  let pageNum = $derived(data.page);
</script>

<svelte:head>
  <title>Resolutions — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">Resolutions</span>
    </div>

    <header class="page-head">
      <span class="kicker">Browse</span>
      <h1>Resolutions</h1>
      <div class="meta">
        <span>{total.toLocaleString()} resolutions indexed</span>
        <span>1946–present</span>
        <span>General Assembly & Security Council</span>
      </div>
    </header>

    <div class="search-grid">
      <aside>
        <div class="filter-block">
          <h4>Body</h4>
          <label class="filter-row"><span><input type="radio" name="body" value="" bind:group={body} on:change={apply} /> Both</span></label>
          <label class="filter-row"><span><input type="radio" name="body" value="GA" bind:group={body} on:change={apply} /> General Assembly</span></label>
          <label class="filter-row"><span><input type="radio" name="body" value="SC" bind:group={body} on:change={apply} /> Security Council</span></label>
        </div>

        <div class="filter-block">
          <h4>Topic</h4>
          <select bind:value={subject_id} on:change={apply}>
            <option value="">Any topic</option>
            {#each data.subjects as s (s.id)}
              <option value={s.id}>{s.name}</option>
            {/each}
          </select>
        </div>

        <div class="filter-block">
          <h4>From date</h4>
          <input type="date" bind:value={from_date} on:change={apply} />
        </div>
        <div class="filter-block">
          <h4>To date</h4>
          <input type="date" bind:value={to_date} on:change={apply} />
        </div>

        <button class="btn ghost sm" on:click={reset}>Reset filters</button>
      </aside>

      <div>
        {#if data.resolutions.items.length === 0}
          <div class="empty">No resolutions match these filters.</div>
        {/if}
        {#each data.resolutions.items as v (v.undl_id)}
          <a class="search-result" href="/resolutions/{v.undl_id}">
            <div>
              <div class="id-line">{v.resolution_code} · {v.body === 'GA' ? 'General Assembly' : 'Security Council'} · {fmtDate(v.vote_date)}</div>
              <h3>{v.title}</h3>
            </div>
            <div class="right">
              <span class="tally-sm">{tallyText(v)}</span>
              <span class="outcome-sm" class:rejected={outcomeLabel(v) === 'Rejected'}>{outcomeLabel(v).toUpperCase()}</span>
              <div class="tally-bar" style="height: 4px; width: 120px;">
                {#each [{c:'var(--for)',v:v.total_yes},{c:'var(--against)',v:v.total_no},{c:'var(--abstain)',v:v.total_abstentions},{c:'var(--didnotvote)',v:v.total_non_voting}] as s}
                  <div class="seg" style="background: {s.c}; width: {((s.v ?? 0) / Math.max(1, (v.total_yes ?? 0) + (v.total_no ?? 0) + (v.total_abstentions ?? 0) + (v.total_non_voting ?? 0))) * 100}%"></div>
                {/each}
              </div>
            </div>
          </a>
        {/each}

        <div class="pager">
          <span>Page {pageNum} of {pageCount.toLocaleString()} · showing {data.resolutions.items.length} of {total.toLocaleString()}</span>
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
    </div>
  </div>
</main>
