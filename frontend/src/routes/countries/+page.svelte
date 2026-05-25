<script>
  let { data } = $props();

  let q = $state('');
  let filtered = $derived.by(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return data.countries;
    return data.countries.filter((c) =>
      (c.name ?? '').toLowerCase().includes(needle) ||
      c.ms_code.toLowerCase().includes(needle)
    );
  });

  // Group by first letter of display name
  let grouped = $derived.by(() => {
    const m = new Map();
    for (const c of filtered) {
      const letter = (c.name ?? c.ms_code).charAt(0).toUpperCase();
      if (!m.has(letter)) m.set(letter, []);
      m.get(letter).push(c);
    }
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b));
  });
</script>

<svelte:head>
  <title>Countries — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">Countries</span>
    </div>

    <header class="page-head">
      <span class="kicker">Browse</span>
      <h1>Countries</h1>
      <div class="meta">
        <span>{data.countries.length} member states</span>
        <span>Sorted alphabetically</span>
      </div>
    </header>

    <div style="padding: 24px 0;">
      <div class="search-input-lg" style="display: flex; align-items: center; gap: 12px; padding: 14px 18px; border: 1px solid var(--rule); background: var(--bg-elev); border-radius: var(--r-1); max-width: 520px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 18px; height: 18px; color: var(--fg-3);"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input bind:value={q} placeholder="Filter by name or code…" style="border: 0; outline: 0; background: transparent; color: var(--fg); flex: 1; font: inherit; font-size: 16px;" />
      </div>
    </div>

    {#if filtered.length === 0}
      <div class="empty">No countries match "{q}".</div>
    {:else}
      {#each grouped as [letter, group]}
        <section class="section" style="padding: 24px 0;">
          <div class="section-head" style="margin-bottom: 8px;">
            <h2 style="font-family: var(--serif); font-weight: 600; font-size: 28px;">{letter}</h2>
            <span class="meta">{group.length}</span>
          </div>
          <div class="country-index">
            {#each group as c (c.ms_code)}
              <a href="/countries/{c.ms_code}">
                <span>{c.name ?? c.ms_code}</span>
                <span class="iso">{c.ms_code}</span>
              </a>
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </div>
</main>
