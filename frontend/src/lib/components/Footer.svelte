<script>
  import Logo from './Logo.svelte';
</script>

<footer class="footer">
  <div class="footer-inner">
    <div style="flex: 1.5; min-width: 240px;">
      <a class="brand" href="/" style="margin-bottom: 12px; text-decoration: none;">
        <Logo variant="wordmark" height={22} />
      </a>
      <p style="margin-top: 12px; max-width: 320px; line-height: 1.5;">
        A free, open-source record of every roll-call vote in the United Nations General Assembly and Security Council. Built by volunteers; sourced from public UN records.
      </p>
    </div>
    <div>
      <h4>Browse</h4>
      <ul>
        <li><a href="/resolutions">All votes</a></li>
        <li><a href="/countries">Countries</a></li>
        <li><a href="/subjects">Topics</a></li>
      </ul>
    </div>
    <div>
      <h4>For developers</h4>
      <ul>
        <li><a href="/api/docs">API</a></li>
        <li><a href="https://digitallibrary.un.org">UN Digital Library</a></li>
        <li><a href="https://github.com">GitHub</a></li>
      </ul>
    </div>
    <div>
      <h4>About</h4>
      <ul>
        <li><a href="/methodology">Methodology</a></li>
        <li><a href="/privacy">Privacy</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-inner" style="margin-top: 28px; font-size: 11px;">
    <span>Data: UN Digital Library · Open Database License</span>
    <span style="margin-left: auto;">© 2026 AllOfOurVotes</span>
  </div>
</footer>
