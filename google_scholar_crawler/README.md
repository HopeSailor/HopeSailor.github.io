# Automated Google Scholar citations

The academic homepage reads the badge JSON from the separate
'google-scholar-stats' branch. This updater queries the [SerpApi Google
Scholar Author API](https://serpapi.com/google-scholar-author-api), not
Google Scholar directly from GitHub Actions.

## Setup (one-time)

1. Create a free SerpApi account at https://serpapi.com/ and retrieve its
   private API key. The free tier currently lists 250 searches/month.
2. In this GitHub repository, open Settings > Secrets and variables > Actions
   > New repository secret. Create **SERPAPI_API_KEY** and paste the key.
   Never share this value in issues, README files or chat messages.
3. Open Actions > Update Google Scholar Citations > Run workflow.
4. Verify the workflow run contains successful offline tests **and** a
   successful Fetch and publish step (not a missing-key warning).
5. On success the workflow automatically updates 'gs_data.json' and
   'gs_data_shieldsio.json' on the 'google-scholar-stats' branch.

The public author ID is wtcf_r4AAAAJ. Scheduled updates are configured for
03:17 UTC daily (subject to GitHub's scheduling delays).

## How it behaves

- No secret: runs offline tests but issues a warning and does not refresh data.
- Invalid API response / unexpected author / citation count below the last
  published count: fails before committing changes.
- Successful refresh: updates existing statistics and known per-paper counts;
  preserves previously published records not returned by the API.
- No third-party Python package dependencies. Python 3.11 standard library.
- The homepage badge may take time to update due to CDN caching.

To test locally without an API key:

    python -m unittest discover -s google_scholar_crawler -p 'test_*.py' -v

GitHub Actions must be enabled and its GITHUB_TOKEN needs Contents write
permission. Branch protection on 'google-scholar-stats' must allow the bot to
push updates. As with any external API, uptime and quota are not guaranteed.
