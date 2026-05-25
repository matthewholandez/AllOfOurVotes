<script>
  import { page as pageStore } from '$app/stores';
  import { tallyText, outcomeLabel, fmtDate } from '$lib/api.js';

  let { data } = $props();

  // Compute "at a glance" stats from the loaded page (cheap approximation)
  let items = $derived(data.resolutions.items);
  let adopted = $derived(items.filter((v) => (v.total_yes ?? 0) > (v.total_no ?? 0)).length);
  let earliestYear = $derived(items.length ? items[items.length - 1].vote_date?.slice(0, 4) : null);
  let latestYear = $derived(items.length ? items[0].vote_date?.slice(0, 4) : null);

  function pageUrl(p) {
    const sp = new URLSearchParams($pageStore.url.searchParams);
    sp.set('page', String(p));
    return `/subjects/${data.subject.id}?` + sp.toString();
  }

  let total = $derived(data.resolutions.total);
  let pageCount = $derived(Math.max(1, Math.ceil(total / data.limit)));
  let pageNum = $derived(data.page);

  // Pipe-delimited names imply hierarchy — surface as a breadcrumb of parts
  let nameParts = $derived(data.subject.name.split('|'));

  let related = $derived(data.subjects.filter((s) => s.id !== data.subject.id).slice(0, 18));
</script>

<svelte:head>
  <title>{data.subject.name} — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <a href="/subjects">Topics</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">{nameParts[nameParts.length - 1]}</span>
    </div>

    <header class="topic-head">
      <div>
        <span class="kicker">Topic № {data.subject.id}</span>
        <h1>{nameParts.map((p) => p.trim().toLowerCase()).map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' · ')}</h1>
        <p class="desc">
          {total.toLocaleString()} resolution{total === 1 ? '' : 's'} indexed under this topic in the UN Digital Library bibliographic record.
        </p>
      </div>
      <div class="topic-summary">
        <h3>At a glance</h3>
        <div class="row"><span class="k">Resolutions</span><span class="v">{total.toLocaleString()}</span></div>
        <div class="row"><span class="k">On this page</span><span class="v">{items.length}</span></div>
        <div class="row"><span class="k">Adopted (page)</span><span class="v" style="color: var(--for);">{adopted} / {items.length}</span></div>
        {#if earliestYear}<div class="row"><span class="k">Earliest (page)</span><span class="v">{earliestYear}</span></div>{/if}
        {#if latestYear}<div class="row"><span class="k">Latest (page)</span><span class="v">{latestYear}</span></div>{/if}
      </div>
    </header>

    <div class="section">
      <div class="section-head">
        <h2>Resolutions</h2>
        <span class="meta">{total.toLocaleString()} indexed</span>
      </div>

      {#if items.length === 0}
        <div class="empty">No resolutions under this topic.</div>
      {/if}
      {#each items as v (v.undl_id)}
        <a class="vote-row" href="/resolutions/{v.undl_id}">
          <span class="date">{fmtDate(v.vote_date)}</span>
          <span class="title">
            {v.title}
            <span class="id">{v.resolution_code} · {v.body === 'GA' ? 'General Assembly' : 'Security Council'}</span>
          </span>
          <span class="tally">{tallyText(v)}</span>
          <span class="outcome" class:rejected={outcomeLabel(v) === 'Rejected'}>{outcomeLabel(v)}</span>
        </a>
      {/each}

      <div class="pager">
        <span>Page {pageNum} of {pageCount.toLocaleString()}</span>
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

    <div class="section">
      <div class="section-head">
        <h2>Other topics</h2>
      </div>
      <div class="topic-row">
        {#each related as t (t.id)}
          <a class="topic-chip" href="/subjects/{t.id}">{t.name}</a>
        {/each}
      </div>
      <div style="margin-top: 16px;">
        <a class="btn text" href="/subjects">See all topics →</a>
      </div>
    </div>
  </div>
</main>
