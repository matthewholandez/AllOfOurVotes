<script>
  import { page } from '$app/stores';
  import Logo from './Logo.svelte';

  let path = $derived($page.url.pathname);
  function isCurrent(prefix) {
    if (prefix === '/') return path === '/';
    return path === prefix || path.startsWith(prefix + '/');
  }
</script>

<nav class="nav">
  <div class="nav-inner">
    <a class="brand" href="/" aria-label="AllOfOurVotes — home">
      <Logo variant="wordmark" height={26} />
    </a>
    <div class="nav-links">
      <a href="/resolutions" class:current={isCurrent('/resolutions') || path === '/'}>Votes</a>
      <a href="/countries" class:current={isCurrent('/countries')}>Countries</a>
      <a href="/subjects" class:current={isCurrent('/subjects')}>Topics</a>
      <a href="/methodology" class:current={isCurrent('/methodology')}>Methodology</a>
    </div>
    <span class="nav-spacer"></span>
    <a class="nav-search" href="/resolutions">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
      </svg>
      <span>Browse resolutions…</span>
      <span class="kbd">⌘ K</span>
    </a>
  </div>
</nav>
