## robots.txt Compliance

Before scraping GradCafe, I manually checked the site's robots.txt file at:

https://www.thegradcafe.com/robots.txt

A screenshot of this check is included in this folder as `screenshot.jpg`.

The robots.txt file includes a general rule for `User-agent: *` with `Allow: /`, while disallowing private/account related paths such as `/signin`, `/register`, `/forgot-password`, `/reset-password`, `/confirm-password`, `/verify-email`, and `/profile`. The scraper is designed to avoid these disallowed paths and only request publicly accessible GradCafe survey pages.

The robots.txt file also includes Cloudflare managed content signals, including `search=yes` and `ai-train=no`. This project does not use scraped content for AI training or model fine tuning. The scraped data is used only for this course assignment and later structured analysis.

The scraper checks robots.txt programmatically using Python's `urllib.robotparser` before requesting GradCafe URLs. It also uses polite scraping behavior, including delays between page requests, no login-protected pages, no CAPTCHA bypassing, no evasion of access controls, and stopping if the site blocks, rate limits, or rejects requests.
