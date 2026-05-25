<script>
  /** @type {{ yes: number|null, no: number|null, abstain: number|null, dnv: number|null }} */
  let { yes = 0, no = 0, abstain = 0, dnv = 0 } = $props();

  // Stable shuffled 28-col grid representing all 193 member states.
  const TOTAL = 252;
  let cells = $derived.by(() => {
    const y = yes ?? 0, n = no ?? 0, a = abstain ?? 0, d = dnv ?? 0;
    const sum = Math.max(1, y + n + a + d);
    const f = Math.round(TOTAL * y / sum);
    const ag = Math.round(TOTAL * n / sum);
    const ab = Math.round(TOTAL * a / sum);
    const arr = [];
    for (let i = 0; i < TOTAL; i++) {
      arr.push(i < f ? 'for' : i < f + ag ? 'against' : i < f + ag + ab ? 'abstain' : 'dnv');
    }
    let s = 7;
    for (let i = arr.length - 1; i > 0; i--) {
      s = (s * 9301 + 49297) % 233280;
      const j = Math.floor((s / 233280) * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  });
</script>

<div class="cartogram">
  {#each cells as cls, i}
    <div class="cell {cls}"></div>
  {/each}
</div>
