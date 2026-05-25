<script>
  import TallyBar from '$lib/components/TallyBar.svelte';
  import Cartogram from '$lib/components/Cartogram.svelte';
  import { tallyText, outcomeLabel, fmtDate, VOTE_LABEL } from '$lib/api.js';

  let { data } = $props();
  let r = $derived(data.resolution);

  let tab = $state('results');

  // Group votes by code
  let groups = $derived.by(() => {
    const g = { Y: [], N: [], A: [], X: [] };
    for (const v of r.votes) g[v.vote]?.push(v);
    for (const k of Object.keys(g)) g[k].sort((a, b) => (a.country_name ?? a.ms_code).localeCompare(b.country_name ?? b.ms_code));
    return g;
  });

  let vetoes = $derived(r.votes.filter((v) => v.vote === 'N' && v.permanent_member === true));

  let total_voting = $derived((r.total_yes ?? 0) + (r.total_no ?? 0) + (r.total_abstentions ?? 0));
  let total_all = $derived(total_voting + (r.total_non_voting ?? 0));
</script>

<svelte:head>
  <title>{r.resolution_code} — {r.title?.slice(0, 80)}</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <a href="/resolutions">Resolutions</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">{r.resolution_code}</span>
    </div>

    <header class="detail-head">
      <span class="id">{r.resolution_code}</span>
      <h1>{r.title}</h1>
      <div class="ctx">
        <span>{r.body === 'GA' ? 'General Assembly' : 'Security Council'}</span>
        {#if r.session}<span>{r.session}th session</span>{/if}
        <span>{fmtDate(r.vote_date)}</span>
        {#if r.subjects?.length}
          <span>Topic: <a href="/subjects/{r.subjects[0].id}" style="color: inherit;">{r.subjects[0].name}</a></span>
        {/if}
      </div>
    </header>

    <section class="detail-grid">
      <div class="detail-main">
        <div class="tally-block">
          <div class="tally-meta" style="margin-bottom: 14px;">
            <span class="total">{tallyText(r)}</span>
            <span class="outcome-text">{outcomeLabel(r)}.</span>
          </div>
          <TallyBar yes={r.total_yes} no={r.total_no} abstain={r.total_abstentions} dnv={r.total_non_voting} />
          <div style="margin-top: 14px; font-size: 12px; color: var(--fg-3);">
            {total_all} of {r.total_ms ?? 193} member states represented.
          </div>
          {#if r.body === 'SC' && vetoes.length}
            <div style="margin-top: 12px; font-size: 13px; color: var(--against); font-family: var(--serif); font-style: italic;">
              Vetoed by {vetoes.map((v) => v.country_name ?? v.ms_code).join(', ')}.
            </div>
          {/if}
        </div>

        <div class="tabs">
          <button class="tab" class:current={tab === 'results'} on:click={() => tab = 'results'}>Results</button>
          <button class="tab" class:current={tab === 'votes'} on:click={() => tab = 'votes'}>All votes</button>
          <button class="tab" class:current={tab === 'details'} on:click={() => tab = 'details'}>Details</button>
          <button class="tab" class:current={tab === 'sources'} on:click={() => tab = 'sources'}>Sources</button>
        </div>

        {#if tab === 'results'}
          <h3 class="overline" style="margin: 0 0 12px;">How the world voted</h3>
          <div style="margin: 8px 0 28px;">
            <Cartogram yes={r.total_yes} no={r.total_no} abstain={r.total_abstentions} dnv={r.total_non_voting} />
          </div>

          {#each [['Y', 'In favor', 'for'], ['N', 'Against', 'against'], ['A', 'Abstained', 'abstain'], ['X', 'Did not vote', 'dnv']] as [code, label, kind]}
            {#if groups[code].length}
              <div style="margin: 28px 0;">
                <h3 style="font-size: 13px; font-weight: 600; margin: 0 0 6px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fg-2); display: flex; align-items: center; gap: 10px;">
                  <span style="width: 9px; height: 9px; background: var(--{kind === 'for' ? 'for' : kind === 'against' ? 'against' : kind === 'abstain' ? 'abstain' : 'didnotvote'}); display: inline-block;"></span>
                  {label} · {groups[code].length}
                </h3>
                <div class="cgrid">
                  {#each groups[code] as v (v.ms_code)}
                    <a class="crow" href="/countries/{v.ms_code}">
                      <span class="nm">{v.country_name ?? v.ms_code}</span>
                      <span class="iso">{v.ms_code}</span>
                    </a>
                  {/each}
                </div>
              </div>
            {/if}
          {/each}
        {/if}

        {#if tab === 'votes'}
          <table class="votes-table">
            <thead>
              <tr><th>Country</th><th>Code</th><th>Vote</th></tr>
            </thead>
            <tbody>
              {#each r.votes as v (v.ms_code)}
                <tr class:veto={v.vote === 'N' && v.permanent_member === true}>
                  <td><a href="/countries/{v.ms_code}">{v.country_name ?? v.ms_code}</a></td>
                  <td class="code">{v.ms_code}</td>
                  <td><span class="their-vote {v.vote}">{VOTE_LABEL[v.vote]}</span></td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}

        {#if tab === 'details'}
          <div class="prose-body">
            <p>
              {r.body === 'GA' ? 'General Assembly' : 'Security Council'} resolution {r.resolution_code}, adopted on {fmtDate(r.vote_date)}{#if r.session} during the {r.session}th session{/if}.
            </p>
            {#if r.agenda}
              <p><strong>Agenda:</strong> {r.agenda}</p>
            {/if}
            {#if r.meeting}
              <p><strong>Meeting:</strong> {r.meeting}</p>
            {/if}
            {#if r.modality}
              <p><strong>Modality:</strong> {r.modality}</p>
            {/if}
            {#if r.committee_report}
              <p><strong>Committee report:</strong> {r.committee_report}</p>
            {/if}
            {#if r.vote_note}
              <p class="muted" style="font-size: 13px;">{r.vote_note}</p>
            {/if}
          </div>
        {/if}

        {#if tab === 'sources'}
          <ul style="padding-left: 18px; margin-top: 14px; font-size: 14px; line-height: 1.7;">
            {#if r.undl_link}
              <li><a href={r.undl_link} target="_blank" rel="noopener">UN Digital Library — {r.resolution_code}</a></li>
            {/if}
            {#if r.meeting}
              <li>Verbatim record: {r.meeting}</li>
            {/if}
            {#if r.drafts?.length}
              <li>Draft documents: {r.drafts.join(', ')}</li>
            {/if}
          </ul>
        {/if}
      </div>

      <aside class="sidebar">
        <h3>Vote details</h3>
        <div class="row"><span class="k">Resolution</span><span class="v mono">{r.resolution_code}</span></div>
        <div class="row"><span class="k">Date</span><span class="v">{fmtDate(r.vote_date)}</span></div>
        {#if r.session}<div class="row"><span class="k">Session</span><span class="v">{r.session}th</span></div>{/if}
        <div class="row"><span class="k">Body</span><span class="v">{r.body === 'GA' ? 'General Assembly' : 'Security Council'}</span></div>
        <div class="row"><span class="k">Voting</span><span class="v">{total_all} / {r.total_ms ?? 193}</span></div>
        <div class="row"><span class="k">Outcome</span><span class="v">{outcomeLabel(r)}</span></div>
        {#if r.modality}<div class="row"><span class="k">Modality</span><span class="v">{r.modality}</span></div>{/if}

        {#if r.subjects?.length}
          <h3 style="margin-top: 28px;">Topics</h3>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">
            {#each r.subjects as s (s.id)}
              <a class="topic-chip" style="font-size: 12px; padding: 4px 9px;" href="/subjects/{s.id}">{s.name}</a>
            {/each}
          </div>
        {/if}

        {#if r.drafts?.length}
          <h3 style="margin-top: 28px;">Drafts</h3>
          <ul style="list-style: none; padding: 0; margin: 0; font-size: 12px; font-family: var(--mono); color: var(--fg-2);">
            {#each r.drafts as d}
              <li style="padding: 4px 0; border-top: 1px solid var(--rule-hair);">{d}</li>
            {/each}
          </ul>
        {/if}

        <h3 style="margin-top: 28px;">Cite</h3>
        <div style="font-family: var(--mono); font-size: 11px; color: var(--fg-2); padding: 10px; background: var(--bg-inset); border: 1px solid var(--rule-hair); word-break: break-all;">
          allofourvotes.org/resolutions/{r.undl_id}
        </div>
        {#if r.undl_link}
          <div style="margin-top: 12px;">
            <a class="btn ghost sm" href={r.undl_link} target="_blank" rel="noopener">UN Digital Library →</a>
          </div>
        {/if}
      </aside>
    </section>
  </div>
</main>
