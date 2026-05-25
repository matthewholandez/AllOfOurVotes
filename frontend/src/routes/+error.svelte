<script>
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>Not found — AllOfOurVotes</title>
</svelte:head>

<main>
  <div class="page">
    <div style="padding: 96px 0; max-width: 560px;">
      <span class="overline">{$page.status} · Error</span>
      <h1 style="font-family: var(--serif); font-size: 44px; font-weight: 600; line-height: 1.1; margin: 12px 0 16px;">
        {$page.status === 404 ? 'Page not found.' : 'Something went wrong.'}
      </h1>
      <p class="prose" style="color: var(--fg-2); margin: 0 0 24px;">
        {$page.error?.message ?? 'The page you requested could not be loaded.'}
      </p>
      <div style="display: flex; gap: 12px;">
        <a class="btn primary" href="/">Home</a>
        <a class="btn ghost" href="/resolutions">Browse resolutions</a>
      </div>
    </div>
  </div>
</main>
