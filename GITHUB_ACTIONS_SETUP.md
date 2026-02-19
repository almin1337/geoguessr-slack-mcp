# GitHub Actions Setup Guide

Follow these steps to deploy the GeoGuessr challenge bot to GitHub Actions.

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `geoguessr-slack-mcp` (or any name you prefer)
3. Choose **Public** (free GitHub Actions) or **Private** (2000 minutes/month free)
4. **Do NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

## Step 2: Push Your Code

Run these commands in your terminal (replace `YOUR_USERNAME` with your GitHub username):

```bash
cd /Users/almindurmis/Documents/Code/geoguessr-slack-mcp

# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/geoguessr-slack-mcp.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If you get authentication errors, you may need to set up a Personal Access Token:
- Go to https://github.com/settings/tokens
- Generate new token (classic) with `repo` scope
- Use the token as your password when pushing

## Step 3: Create GitHub Gist for State Storage

Since GitHub Actions doesn't persist files between runs, we'll use a GitHub Gist to store state.

1. Go to https://gist.github.com
2. Filename: `state.json`
3. Content: `{}`
4. Choose **Create public gist** or **Create secret gist** (secret is recommended)
5. Click **Create gist**
6. Copy the Gist ID from the URL: `https://gist.github.com/YOUR_USERNAME/GIST_ID`
   - The Gist ID is the long hash after your username

## Step 4: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Name: `GeoGuessr Bot State Storage`
4. Select scopes:
   - ✅ `gist` (to read/write Gists)
5. Click **Generate token**
6. **Copy the token immediately** (you won't see it again!)

## Step 5: Add GitHub Secrets

1. Go to your repository: `https://github.com/YOUR_USERNAME/geoguessr-slack-mcp`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these secrets:

   | Secret Name | Value |
   |------------|-------|
   | `GEOGUESSR_COOKIE` | Your `_ncfa` cookie value from GeoGuessr |
   | `SLACK_BOT_TOKEN` | Your Slack bot token (starts with `xoxb-`) |
   | `SLACK_CHANNEL_ID` | Your Slack channel ID (starts with `C`) |
   | `GITHUB_GIST_ID` | The Gist ID from Step 3 |
   | `GITHUB_TOKEN` | The Personal Access Token from Step 4 |

## Step 6: Adjust Timezone (If Needed)

The workflow runs hourly from 8:00-15:00 UTC on weekdays. If you need a different timezone:

1. Open `.github/workflows/daily-challenge.yml`
2. Find the cron schedule: `'0 8-15 * * 1-5'`
3. Adjust the hours based on your timezone:
   - **UTC+1** (e.g., Central Europe): `'0 7-14 * * 1-5'` (8:00 local = 7:00 UTC)
   - **UTC-5** (e.g., EST): `'0 13-20 * * 1-5'` (8:00 local = 13:00 UTC)
   - **UTC-8** (e.g., PST): `'0 16-23 * * 1-5'` (8:00 local = 16:00 UTC)
4. Commit and push:
   ```bash
   git add .github/workflows/daily-challenge.yml
   git commit -m "Adjust timezone for local time"
   git push
   ```

## Step 7: Test the Workflow

1. Go to your repository → **Actions** tab
2. Click **Daily GeoGuessr Challenge** workflow
3. Click **Run workflow** → **Run workflow** (manual trigger)
4. Watch it run! It should create a challenge and post to Slack.

## Troubleshooting

### Workflow doesn't run automatically
- Check that the cron schedule is correct
- GitHub Actions may take a few minutes to start scheduled runs
- Verify the workflow file is in `.github/workflows/`

### State not persisting
- Verify `GITHUB_GIST_ID` and `GITHUB_TOKEN` secrets are set correctly
- Check the Gist exists and is accessible
- Look at workflow logs for Gist API errors

### Challenge creation fails
- Verify `GEOGUESSR_COOKIE` is correct (get fresh cookie from GeoGuessr)
- Check workflow logs for API errors
- Browser fallback should work if API fails

### Slack posting fails
- Verify `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` are correct
- Check bot has `chat:write` permission in Slack
- Verify channel ID (not channel name)

## Monitoring

- **Workflow runs**: Check the **Actions** tab in your repository
- **State**: View your Gist to see current state
- **Logs**: Click any workflow run to see detailed logs

## Manual Trigger

You can manually trigger the workflow anytime:
1. Go to **Actions** → **Daily GeoGuessr Challenge**
2. Click **Run workflow** → **Run workflow**

This is useful for testing or creating extra challenges!
