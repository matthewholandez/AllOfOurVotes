<script>
  import TallyBar from '$lib/components/TallyBar.svelte';
  import { tallyText, outcomeLabel, fmtDate } from '$lib/api.js';

  let { data } = $props();

  let featured = $derived(data.resolutions.items[0]);
  let rest = $derived(data.resolutions.items.slice(1));

  // Topic chips: 14 longest-running subjects (by id, since lower id ≈ alphabetical anchor)
  let topicChips = $derived(data.subjects.slice(0, 14));
</script>

<svelte:head>
  <title>AllOfOurVotes — every UN vote, on the record</title>
</svelte:head>

<main>
  <div class="page">
    <section class="hero">
      <h1>Every vote in the General Assembly, on the record.</h1>
      <p class="lede">
        AllOfOurVotes turns the United Nations' public voting record into something you can search, read, and cite. {data.resolutions.total.toLocaleString()} resolutions, {data.subjects.length} topics, 203 member states.
      </p>
      <div class="cta">
        <a class="btn primary" href="/resolutions">Browse resolutions</a>
        <a class="btn ghost" href="/countries">Find your country</a>
      </div>
    </section>
  </div>

  {#if featured}
    <div class="page">
      <a class="featured" href="/resolutions/{featured.undl_id}">
        <div>
          <span class="id">{featured.resolution_code} · {fmtDate(featured.vote_date)}</span>
          <h3>{featured.title}</h3>
          <p class="lede">
            Adopted by the {featured.body === 'GA' ? 'General Assembly' : 'Security Council'} with {featured.total_yes ?? 0} in favor, {featured.total_no ?? 0} against, and {featured.total_abstentions ?? 0} abstentions.
          </p>
          <div style="margin-top: 16px;">
            <span class="btn text">Read the vote →</span>
          </div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 14px; justify-content: center;">
          <div class="tally-meta">
            <span class="total" style="font-size: 30px;">{tallyText(featured)}</span>
            <span class="outcome-text" style="font-size: 16px;">{outcomeLabel(featured)}.</span>
          </div>
          <TallyBar
            yes={featured.total_yes}
            no={featured.total_no}
            abstain={featured.total_abstentions}
            dnv={featured.total_non_voting}
            showLegend={false}
          />
          <span class="muted" style="font-size: 12px;">
            {featured.total_yes ?? 0} in favor · {featured.total_no ?? 0} against · {featured.total_abstentions ?? 0} abstained
          </span>
        </div>
      </a>
    </div>
  {/if}

  <div class="page">
    <section class="section">
      <div class="section-head">
        <h2>Recent resolutions</h2>
        <span class="meta">{data.resolutions.total.toLocaleString()} indexed</span>
      </div>
      {#each rest as v (v.undl_id)}
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
      <div style="margin-top: 20px;">
        <a class="btn ghost sm" href="/resolutions">Show all {data.resolutions.total.toLocaleString()} resolutions →</a>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>Browse by topic</h2>
        <span class="meta">{data.subjects.length} topics indexed</span>
      </div>
      <div class="topic-row">
        {#each topicChips as t (t.id)}
          <a class="topic-chip" href="/subjects/{t.id}">{t.name}</a>
        {/each}
      </div>
      <div style="margin-top: 16px;">
        <a class="btn text" href="/subjects">See all topics →</a>
      </div>
    </section>
  </div>
</main>
