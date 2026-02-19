# Check GitHub Actions Schedule Configuration

## Steps to Verify Scheduled Workflows Are Enabled

### 1. Check Repository Actions Settings
1. Go to: https://github.com/almin1337/geoguessr-slack-mcp/settings/actions
2. Under "Actions permissions", ensure:
   - ✅ "Allow all actions and reusable workflows" is selected
   - ✅ "Allow GitHub Actions to create and approve pull requests" (if you want that)
3. Scroll down to "Workflow permissions":
   - ✅ "Read and write permissions" should be selected
   - ✅ "Allow GitHub Actions to create and approve pull requests" (if needed)

### 2. Check if Workflow is Disabled
1. Go to: https://github.com/almin1337/geoguessr-slack-mcp/actions
2. Click on "Daily GeoGuessr Challenge"
3. Look for a yellow banner saying "This workflow was disabled"
4. If you see it, click "Enable workflow"

### 3. Verify Workflow File Location
- ✅ File is at: `.github/workflows/daily-challenge.yml`
- ✅ File is on `main` branch (default branch)
- ✅ File has valid YAML syntax

### 4. Check Cron Syntax
Current test schedule: `*/5 * * * *` (every 5 minutes)
- This should trigger every 5 minutes
- If it doesn't work, GitHub isn't recognizing the schedule

### 5. Repository Activity
- Scheduled workflows in public repos can disable after 60 days of inactivity
- Your repository is active (recent commits), so this shouldn't be an issue

### 6. Alternative: Check Workflow File Directly
View the raw workflow file to ensure it's correct:
https://github.com/almin1337/geoguessr-slack-mcp/blob/main/.github/workflows/daily-challenge.yml

## If Schedule Still Doesn't Work

If after checking all the above, scheduled runs still don't appear:

1. **Wait up to 1 hour** - GitHub can take time to recognize schedules
2. **Check tomorrow morning** - The first scheduled run might happen at the next scheduled time
3. **Try a different approach** - Use a different scheduling service or run locally

## Current Status
- Workflow file: ✅ Correct location and syntax
- Cron schedule: ✅ Valid syntax (`*/5 * * * *` for testing)
- Repository: ✅ Public
- Manual trigger: ✅ Works
- Scheduled trigger: ❌ Not working yet
