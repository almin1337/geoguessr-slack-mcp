# GitHub Actions Workflow Troubleshooting

## Issue: Scheduled workflow not running automatically

### Check 1: Verify workflow is enabled
1. Go to https://github.com/almin1337/geoguessr-slack-mcp/actions
2. Click on "Daily GeoGuessr Challenge" workflow
3. Look for a yellow banner saying "This workflow was disabled manually"
4. If you see it, click "Enable workflow"

### Check 2: Verify workflow file is on default branch
- The workflow file must be on the `main` branch (it is)
- Scheduled workflows don't run from other branches or PRs

### Check 3: GitHub schedule recognition delay
- GitHub can take **15 minutes to over an hour** to recognize a new or updated cron schedule
- If you just created/updated the workflow, wait up to an hour
- The schedule might not appear in the UI until the first scheduled run completes

### Check 4: Verify cron schedule
Current schedule: `'0 7-14 * * 1-5'`
- Runs at: 7:00, 8:00, 9:00, 10:00, 11:00, 12:00, 13:00, 14:00 UTC
- Which equals: 8:00, 9:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00 CET (winter)
- Only runs on weekdays (Monday-Friday)

### Check 5: Test with a more frequent schedule
To quickly verify GitHub recognizes the schedule, temporarily change the cron to run every 5 minutes:
```yaml
- cron: '*/5 * * * *'  # Every 5 minutes for testing
```
Then change it back after confirming it works.

### Check 6: Force resync
Make a small commit (like adding a comment) to force GitHub to re-evaluate the workflow:
```bash
git commit --allow-empty -m "Force workflow resync"
git push
```

### Check 7: Repository visibility
- For free GitHub accounts, scheduled workflows require a **public repository**
- Your repository is public, so this should be fine

## Current Status
- Workflow file: ✅ On main branch
- Cron schedule: ✅ `'0 7-14 * * 1-5'` (7:00-14:00 UTC = 8:00-15:00 CET)
- Repository: ✅ Public
- Manual trigger: ✅ Works (you've tested this)

## Next Steps
1. Check if workflow is enabled (Check 1)
2. Wait up to an hour for GitHub to recognize the schedule
3. Check the Actions tab tomorrow morning to see if it ran at 8:00 CET (7:00 UTC)
