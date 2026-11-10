1shot Server Tag Statistics Bot
===============================

Railway deployment:
1. Upload these files to a GitHub repository.
2. In Railway, create a new project -> Deploy from GitHub Repo.
3. Add these Variables in Railway:
     DISCORD_TOKEN
     GUILD_ID
     CHANNEL_ID
     MESSAGE_ID=0
4. Deploy. Railway will install requirements.txt and run the Procfile worker.

Discord Developer Portal:
- Enable the Server Members Intent under Bot -> Privileged Gateway Intents.
- Invite the bot with View Channels, Send Messages, Embed Links, and Read Message History.
- The bot must be able to view the statistics channel.

Important:
The bot depends on Discord supplying user.primary_guild in member REST/Gateway
payloads. Discord may omit optional user fields in some payloads. Check Railway
deployment logs after the first run to confirm that the initial scan detects tags.
This bot does not bypass Discord API limitations or retrieve hidden tag data.

MESSAGE_ID:
- Keep 0 to let the bot create a new embed message.
- After the first run, you can set MESSAGE_ID to the created message ID to reuse it.
