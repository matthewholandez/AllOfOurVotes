<main>
  <div class="page">
    <div class="crumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <span style="color: var(--fg);">Methodology</span>
    </div>

    <header class="page-head">
      <span class="kicker">About</span>
      <h1>Methodology</h1>
      <div class="meta">
        <span>How the data is sourced</span>
        <span>How votes are categorised</span>
      </div>
    </header>

    <section class="detail-grid">
      <div class="detail-main">
        <div class="prose-body">
          <p>
            AllOfOurVotes mirrors the public roll-call record of the United Nations General Assembly and Security Council. Source data comes from the <a href="https://digitallibrary.un.org" target="_blank" rel="noopener">UN Digital Library</a> and is normalised into a relational store. No vote is re-tallied or re-interpreted; we surface what the official record says.
          </p>
          <p>
            <strong>Member states.</strong> 203 codes are tracked, including current and historical entities. Country names are time-ranged — a 1983 vote by "Democratic Kampuchea" remains under that name, even though the seat is now held by Cambodia.
          </p>
          <p>
            <strong>Vote codes.</strong> <em>Yes</em>, <em>No</em>, <em>Abstain</em>, and <em>Non-voting</em> are stored as the source single letters Y, N, A, X. Outcome ("Adopted" / "Rejected") is derived from the vote tally, not re-asserted by us.
          </p>
          <p>
            <strong>Vetoes.</strong> Security Council resolutions are flagged as vetoed when a permanent member (China, France, Russia, the United Kingdom, or the United States) votes against.
          </p>
          <p>
            <strong>Known gaps.</strong> About 250 votes during the United Arab Republic period (1958–1971) have ambiguous country-name resolution; those rows fall back to the ISO code.
          </p>
        </div>
      </div>

      <aside class="sidebar">
        <h3 id="sources">Sources</h3>
        <div class="row"><span class="k">Primary</span><span class="v">UN Digital Library</span></div>
        <div class="row"><span class="k">Period</span><span class="v">1946 – present</span></div>
        <div class="row"><span class="k">Bodies</span><span class="v">GA & SC</span></div>

        <h3 style="margin-top: 28px;">License</h3>
        <p class="small" style="margin: 6px 0 0;">
          Voting data is in the public domain. Site code is open-source.
        </p>
      </aside>
    </section>
  </div>
</main>
