1shot VC Guard + Tag Rotator Preview Module

FILES
- 1shot_vc_guard_tag_rotator.py: merged bot source (existing VC Guard + tag-rotator admin queue/preview module)
- requirements.txt: Python dependency
- Procfile: Railway worker start command

RAILWAY SETUP
1. Upload these files to your Railway project/repository.
2. Set environment variable DISCORD_TOKEN to your bot token.
3. Add a persistent Railway Volume and mount it at /app/data.
4. Set environment variable DATA_DIR=/app/data.
5. Deploy as a worker service.
6. Invite the bot with applications.commands and the permissions required by your existing VC Guard features.

TAG ROTATOR COMMANDS
- /tagrotator_panel
- /tagrotator_add symbol_label:<label>
- /tagrotator_remove symbol_label:<label>
- /tagrotator_interval seconds:<30-86400>
- /tagrotator_start
- /tagrotator_stop

DEFAULT INTERVAL: 30 seconds.

IMPORTANT LIMITATION
This module stores an administrator-managed ordered queue and advances a preview index. It does NOT change the actual Discord server-tag badge. Discord's documented Bot API does not expose a supported endpoint for changing that badge. The labels entered are queue labels, not actual Discord badge assets. Do not use a user token/self-bot or unofficial private endpoints to attempt badge changes.

DATABASE
The module adds two SQLite tables to the existing database file: tag_rotator_config and tag_rotator_symbols. Existing VC Guard tables and features are retained.
