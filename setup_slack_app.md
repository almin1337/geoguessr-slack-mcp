# Setting Up Slack App for GeoGuessr Integration

Follow these steps to create a Slack app and get the bot token:

## Step 1: Create a Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: "GeoGuessr Daily Challenge"
5. Select your workspace
6. Click "Create App"

## Step 2: Configure Bot Token Scopes

1. In your app settings, go to "OAuth & Permissions" in the left sidebar
2. Scroll down to "Scopes" → "Bot Token Scopes"
3. Add the following scopes:
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic information about public channels
   - `chat:write` - Send messages as the app
   - `users:read` - View people in a workspace

## Step 3: Install App to Workspace

1. Scroll up to "OAuth Tokens for Your Workspace"
2. Click "Install to Workspace"
3. Review the permissions and click "Allow"
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
5. Save this token - you'll need it for the `SLACK_BOT_TOKEN` environment variable

## Step 4: Get Channel ID

1. Open Slack and navigate to your channel
2. Right-click on the channel name in the sidebar
3. Select "View channel details" (or click the channel name)
4. Scroll down to find the "Channel ID" (starts with `C`)
5. Copy this ID for the `SLACK_CHANNEL_ID` environment variable

Alternatively:
- You can also get the channel ID from the URL: `https://yourworkspace.slack.com/archives/C1234567890`
- The part after `/archives/` is the channel ID

## Step 5: Invite Bot to Channel

1. In your Slack channel, type `/invite @GeoGuessr Daily Challenge`
2. Or manually add the bot: Channel settings → Integrations → Add apps → Find your app

## Done!

Now you have:
- ✅ Bot Token (`xoxb-...`)
- ✅ Channel ID (`C...`)
- ✅ Bot installed and invited to channel

Use these values in your `.env` file or environment variables.
