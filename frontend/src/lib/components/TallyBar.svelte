<script>
  /** @type {{ yes: number|null, no: number|null, abstain: number|null, dnv: number|null, height?: number, showLegend?: boolean }} */
  let { yes = 0, no = 0, abstain = 0, dnv = 0, height = 18, showLegend = true } = $props();

  let y = $derived(yes ?? 0);
  let n = $derived(no ?? 0);
  let a = $derived(abstain ?? 0);
  let d = $derived(dnv ?? 0);
  let total = $derived(Math.max(1, y + n + a + d));
  let pct = $derived((v) => (v / total) * 100);
</script>

<div class="tally-stack">
  <div class="tally-bar" style="height: {height}px;">
    <div class="seg" style="background: var(--for); width: {pct(y)}%"></div>
    <div class="seg" style="background: var(--against); width: {pct(n)}%"></div>
    <div class="seg" style="background: var(--abstain); width: {pct(a)}%"></div>
    <div class="seg" style="background: var(--didnotvote); width: {pct(d)}%"></div>
  </div>
  {#if showLegend}
    <div class="tally-legend">
      <span><span class="dot" style="background: var(--for);"></span>{y} in favor</span>
      <span><span class="dot" style="background: var(--against);"></span>{n} against</span>
      <span><span class="dot" style="background: var(--abstain);"></span>{a} abstained</span>
      <span><span class="dot" style="background: var(--didnotvote);"></span>{d} did not vote</span>
    </div>
  {/if}
</div>
