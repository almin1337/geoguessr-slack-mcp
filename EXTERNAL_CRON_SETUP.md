# Trigger Workflow via External Cron (No Laptop Required)

The workflow is triggered by an **external cron service** (e.g. cron-job.org) that calls the GitHub API at 9:20 and 12:20 CET on weekdays. No GitHub schedule, no laptop needed.

---

## Option 1: cron-job.org (Free, No Credit Card)

### Step 1: Create a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. **Generate new token** → **Generate new token (classic)**
3. Name: `Trigger GeoGuessr workflow`
4. Expiration: No expiration (or 1 year)
5. Scopes: enable **`repo`** and **`workflow`**
6. Generate token and **copy it** (you won’t see it again)

### Step 2: Create cron jobs at cron-job.org

1. Go to https://cron-job.org and create a free account (or log in).
2. **Create first job – 9:20 CET**
   - **Title:** GeoGuessr Challenge 9:20
   - **URL:**  
     `https://api.github.com/repos/almin1337/geoguessr-slack-mcp/actions/workflows/daily-challenge.yml/dispatches`
   - **Schedule:**  
     - Time: **09:20**  
     - Timezone: **Europe/Paris** (CET/CEST)  
     - Days: **Monday–Friday** (weekdays only)
   - **Request method:** **POST**
   - **Request headers:**
     - `Accept`: `application/vnd.github.v3+json`
     - `Authorization`: `token YOUR_GITHUB_TOKEN`
     - `Content-Type`: `application/json`
   - **Request body:**  
     `{"ref":"main"}`
   - Save the job.

3. **Create second job – 12:20 CET**
   - Same as above, but:
   - **Title:** GeoGuessr Challenge 12:20
   - **Schedule → Time:** **12:20** (same timezone and weekdays)
   - Same URL, headers, and body.
   - Save the job.

### Step 3: Verify

- After 9:20 or 12:20 CET on a weekday, check:  
  https://github.com/almin1337/geoguessr-slack-mcp/actions  
- You should see a new run triggered by “workflow_dispatch” (and in the cron-job.org dashboard you’ll see the request was sent).

---

## Option 2: EasyCron or Other “HTTP cron” Services

Any service that can send an HTTP POST on a schedule works. Use the same details:

- **URL:**  
  `https://api.github.com/repos/almin1337/geoguessr-slack-mcp/actions/workflows/daily-challenge.yml/dispatches`
- **Method:** POST
- **Headers:**
  - `Accept: application/vnd.github.v3+json`
  - `Authorization: token YOUR_GITHUB_TOKEN`
  - `Content-Type: application/json`
- **Body:** `{"ref":"main"}`

Schedule two jobs: one at 9:20 CET and one at 12:20 CET, weekdays only (Europe/Paris or your CET timezone).

---

## Security Notes

- The token must have **repo** and **workflow** scope so it can trigger the workflow.
- Store the token only in the cron service’s “headers” or “secret” field; don’t commit it.
- If the token is compromised, revoke it at https://github.com/settings/tokens and create a new one, then update the cron job.

---

## Summary

| What                | Value                                                                 |
|---------------------|-----------------------------------------------------------------------|
| API endpoint        | `POST https://api.github.com/repos/almin1337/geoguessr-slack-mcp/actions/workflows/daily-challenge.yml/dispatches` |
| Header `Authorization` | `token YOUR_GITHUB_TOKEN`                                          |
| Body                | `{"ref":"main"}`                                                      |
| Times (CET)         | 9:20 and 12:20                                                        |
| Days                | Monday–Friday                                                          |

Once these two cron jobs are set up, your workflow will run at 9:20 and 12:20 CET on weekdays **without using your laptop** and without relying on GitHub’s built-in schedule.
