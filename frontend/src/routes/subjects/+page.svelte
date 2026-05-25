<script>
  let { data } = $props();

  let q = $state('');
  let filtered = $derived.by(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return data.subjects;
    return data.subjects.filter((s) => s.name.toLowerCase().includes(needle));
  });

  // Group by first letter
  let grouped = $derived.by(() => {
    const m = new Map();
    for (const s of filtered) {
      const letter = s.name.charAt(0).toUpperCase();
      if (!m.has(letter)) m.set(letter, []);
      m.get(letter).push(s);
    }
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b));
  });
</script>

<svelte:head>
  <title>Topics — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">Topics</span>
    </div>

    <header class="page-head">
      <span class="kicker">Browse</span>
      <h1>Topics</h1>
      <div class="meta">
        <span>{data.subjects.length} topics indexed</span>
        <span>Sourced from UN bibliographic records</span>
      </div>
    </header>

    <div style="padding: 24px 0;">
      <div class="search-input-lg" style="display: flex; align-items: center; gap: 12px; padding: 14px 18px; border: 1px solid var(--rule); background: var(--bg-elev); border-radius: var(--r-1); max-width: 520px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 18px; height: 18px; color: var(--fg-3);"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input bind:value={q} placeholder="Filter topics…" style="border: 0; outline: 0; background: transparent; color: var(--fg); flex: 1; font: inherit; font-size: 16px;" />
      </div>
    </div>

    {#if filtered.length === 0}
      <div class="empty">No topics match "{q}".</div>
    {:else}
      {#each grouped as [letter, group]}
        <section class="section" style="padding: 24px 0;">
          <div class="section-head" style="margin-bottom: 8px;">
            <h2 style="font-family: var(--serif); font-weight: 600; font-size: 24px;">{letter}</h2>
            <span class="meta">{group.length}</span>
          </div>
          <div class="subject-index">
            {#each group as s (s.id)}
              <a href="/subjects/{s.id}">
                <span>{s.name}</span>
                <span class="id">№{s.id}</span>
              </a>
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </div>
</main>
