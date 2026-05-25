<script>
  /** @type {{ variant?: 'wordmark' | 'mark' | 'stacked' | 'monogram', height?: number }} */
  let { variant = 'wordmark', height = 22 } = $props();
</script>

{#if variant === 'mark'}
  <svg viewBox="0 0 32 32" {height} aria-label="AllOfOurVotes" role="img" style="display:block">
    <rect x="0" y="0" width="14" height="32" fill="currentColor"/>
    <rect x="18" y="0" width="6" height="32" fill="currentColor" opacity="0.55"/>
    <rect x="27" y="0" width="3" height="32" fill="currentColor" opacity="0.30"/>
  </svg>
{:else if variant === 'stacked'}
  <svg viewBox="0 0 200 100" {height} aria-label="AllOfOurVotes.org" role="img" style="display:block">
    <g transform="translate(0,8)">
      <rect x="0" y="0" width="22" height="50" fill="currentColor"/>
      <rect x="28" y="0" width="10" height="50" fill="currentColor" opacity="0.55"/>
      <rect x="42" y="0" width="5" height="50" fill="currentColor" opacity="0.30"/>
    </g>
    <text x="0" y="92" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" font-size="22" letter-spacing="-0.5" fill="currentColor">
      AllOfOurVotes<tspan font-weight="400" opacity="0.55">.org</tspan>
    </text>
  </svg>
{:else if variant === 'monogram'}
  <svg viewBox="0 0 64 64" {height} aria-label="AOV" role="img" style="display:block">
    <rect x="0" y="0" width="64" height="64" fill="currentColor"/>
    <text x="32" y="42" text-anchor="middle" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" font-size="22" letter-spacing="-0.5" fill="var(--bg)">AOV</text>
  </svg>
{:else}
  <svg viewBox="0 0 300 40" {height} aria-label="AllOfOurVotes.org" role="img" style="display:block">
    <g transform="translate(0,4)">
      <rect x="0" y="0" width="14" height="32" fill="currentColor"/>
      <rect x="18" y="0" width="6" height="32" fill="currentColor" opacity="0.55"/>
      <rect x="27" y="0" width="3" height="32" fill="currentColor" opacity="0.30"/>
    </g>
    <text x="46" y="28" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" font-size="24" letter-spacing="-0.6" fill="currentColor">
      AllOfOurVotes<tspan font-weight="400" opacity="0.55">.org</tspan>
    </text>
  </svg>
{/if}
