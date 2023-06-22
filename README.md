# Ember's Discord Registration Bot

This is a Python bot that allows users to register a TrinityCore account by direct messaging a bot with specific commands. Users' Discord identifiers are tied to the game account and both the Discord identifier and the TrinityCore username are checked for duplicates.

### Current Compatibility
- [TrinityCore 3.3.5](https://github.com/TrinityCore/TrinityCore)
- [Azerothcore 3.3.5](https://github.com/AzerothCore/)

## Requirements
- Python3
   - Pip Packages: `mysql.connector`, `discord` via `pip install`
   - Easy Linux Command that installs the packages for you: `pip install mysql.connector && pip install discord`

## Installation Instructions

### Create a Discord Bot
1. Access Discord's [Developer Portal](https://discord.com/developers/applications) and create a `New Application`.
2. Navigate to the `Bot` section of your application settings and click `Add Bot`.
   - Set the username and profile icon of the bot.
   - Reset and save your bots `Token`.
   - No permissions are required, as the bot interacts via direct messages with users.
3. Navigate to `OAuth2` -> `URL Generator`.
   - In the `Scopes` section:
      - [x] `bot`
   - Copy the `Generated URL` and paste it into your browser to invite it to your server.
4. The bot should now be visible (_though offline_) in the server you invited it to.

### Run the Bot
1. Edit the bot config file, [registration.cfg](/registration.cfg).
   - The `[mysql]` settings should match the database settings of the TrinityCore MySQL server.
      - There are potential issues with setting `host = localhost`. Use `127.0.0.1` instead.
      - A blank password will connect via the unix socket.
   - The `[discord]` settings should match the following:
      - `apiKey` is the bot `Token` generated above.
      - `targetServer` is the [ID of a Discord server](https://www.remote.tools/remote-work/how-to-find-discord-id) the bot is in.
      - `logsChannel` is the [ID of a Discord channel](https://www.remote.tools/remote-work/how-to-find-discord-id) in the server the bot is in.
      - `staff` is the [ID of a Discord role](https://www.remote.tools/remote-work/how-to-find-discord-id) required for "givemepowers"
   - The `[soap]` settings should match the following:
      - `host` is the SOAP.IP in worldserver.conf
      - `user` is a user capable of using account create, and set password commands in-game.
      - `pass` is the password for that user.
      - `port` is SOAP.Port in worldserver.conf
      - `soapRBAC` is the RBAC role provided when "givemepowers" is called.
2. Edit the worldserver config file, worldserver.conf
   - 1. Set SOAP.Enabled = 1
3. Run the bot.
   - Ensure [Requirements](#requirements) are met.
   - Run `discord_bot.py`

### Registering via the Bot
1. Direct message the bot using the following syntax:
   - `register <username> <password>`
2. If any errors occur during registration, the bot will let the user know.

### Changing Password via the Bot
1. Direct message the bot using the following syntax:
   - `account set password <newpassword> <newpassword>`
2. If any errors occur, the bot will inform the user.

### Distributing Staff Powers via the Bot
1. Direct message the bot using the following syntax:
   - `givemepowers`
2. If any errors occur, the bot will inform the user.

## To Do
- Give a command to authorize GM accounts under the right circumstances
- Add OS specific instructions
- Provide better instructions to maintain safe user permissions and practices

## Disclaimer
Anyone who uses this on their server is capable of logging passwords. Encourage your users to provide throwaway passwords or unique passwords. This is a potential way to steal credentials, so it's ethical that all users should be aware and instructed to create unique passwords for your server.

This bot uses the SOAP API to register accounts. So long as your core can handle the above commands and can support SOAP, this bot will work with it.

## Contribute
If you'd like to contribute, please fork and create a pull request. Your code will be reviewed and then merged with the main branch.
