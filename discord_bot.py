import configparser, asyncio, telnetlib, time, requests # Standard Libs
import discord, mysql.connector # Requires from pip3: discord-py

### Setup
config = configparser.ConfigParser()
config.read('registration.cfg')

mysqlHost = config['mysql']['host']
mysqlauthDB = config['mysql']['authdb']
mysqlcharDB = config['mysql']['chardb']
mysqlUser = config['mysql']['user']
mysqlPass = config['mysql']['pass']
mysqlPort = config['mysql']['port']
apiKey = config['discord']['apiKey']
discordServerID = int(config['discord']['targetServer'])
logsChannelID = int(config['discord']['logsChannel'])
staffRoleID = config['discord']['staff'] # Role ID of Staff needed for "givemepowers"
# IN WORLDSERVER.CONF, PLEASE SET SOAP.ENABLED = 1
soapHost = config['soap']['host']
soapUser = config['soap']['user'] # User, pass is the user/pass of an account that can access the console/in-game and create/set passwords, accounts, etc.
soapPass = config['soap']['pass']
soapPort = config['soap']['port']
soapRBAC = config['soap']['rbac'] # The RBAC provided when "givemepowers" is called.
## End Setup

intents=discord.Intents.default()
intents.members = True
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

# send_message, arg1 is string, arg2 is output channel
async def send_message(arg1, arg2):
    channel = client.get_channel(arg2)
    await channel.send(arg1)

# sterilize user input so nobody nukes the db
def sterilize(parameter):
    str(parameter)
    parameter = parameter.replace("%;","") # Replace the character ";" with nothing. Does this really need escaping?
    parameter = parameter.replace("`","") # Replace the character "`" with nothing.
    parameter = parameter.replace("(%a)'","%1`") # For any words that end with ', replace the "'" with "`"
    parameter = parameter.replace("(%s)'(%a)","%1;%2") # For any words that have a space, then the character "'" and then letters, replace the "'" with a ";".
    parameter = parameter.replace("'","") # Replace the character "'" with nothing.
    parameter = parameter.replace("(%a)`","%1''") # For any words that end with "`", replace the "`" with "''"
    parameter = parameter.replace("(%s);(%a)","%1''%2") # For any words that have a space, then the character ";" and then letters, replace the ";" with "''".
    return parameter

# registration function put here for readability
async def register(message):
    messageParameters = message.content.split(" ")
    print("registering")
    #print(len(messageParameters))
    if len(messageParameters) != 3:
        logString = ("[Register]: User : " + str(message.author) + " failed to register with following input : " + messageParameters[0] + " " + messageParameters[1] + " <REDACTED>.")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Register]: There was an error processing your command.\nPlease input `register <username> <password>`.\nExample: `register marco polo` would make a username marco with password polo.")
        return
        
    discordid=str(message.author.id).upper()
    wowUsername = sterilize(messageParameters[1])
    wowPassword = sterilize(messageParameters[2])
    concat_string = "account create " + wowUsername + " " + wowPassword
    
    # Discord ID check
    # SQL STUFF STARTS HERE
    connection = mysql.connector.connect(user=mysqlUser, password=mysqlPass, host=mysqlHost, database=mysqlauthDB, port=mysqlPort) # db connection
    cursor = connection.cursor() # our cursor that selects n stuff
    registrationSQL = "SELECT username, email FROM account WHERE username = %s OR email = %s" # check if username OR email(discordid) exists
    checkval = (wowUsername, discordid) # this is how we pass multiple variables to the execute script
    cursor.execute(registrationSQL,checkval)
    result = cursor.fetchall()
    connection.commit() # We need this or the script will cache the query.
    if len(result) != 0:
        if result[0][0] == wowUsername: #check if username exists
            logString = ("[Register]: User : " + str(message.author) + " failed to register because that username already exists.")
            print(logString)
            await send_message(logString, logsChannelID)
            await message.author.send("[Register]: An account with that username already exists.")
            return
        elif result[0][1] == discordid: # check if user with discordid exists
            logString = ("[Register]: User : " + str(message.author) + " failed to register because their discordID already exists.")
            print(logString)
            await send_message(logString, logsChannelID)
            await message.author.send("[Register]: An account with your Discord ID already exists.")
            return    
    
    
    soap_url = "http://" + soapUser + ":"  + soapPass + "@" + soapHost + ":" + soapPort + "/"
    payload = """<SOAP-ENV:Envelope  
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
    xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/1999/XMLSchema" 
    xmlns:ns1="urn:AC">
    <SOAP-ENV:Body>
	<ns1:executeCommand>
	    <command>""" + concat_string + """</command>
	</ns1:executeCommand>
    </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>"""
    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }
    # POST request
    response = requests.request("POST", soap_url, headers=headers, data=payload)
    registrationSQL = "UPDATE account SET email = (%s) WHERE username = (%s);" # there is no command to set email which is our discordid link. sql query here to update account email.
    val = [
    discordid,
    wowUsername,
    ]
    cursor.execute(registrationSQL, val)
    connection.commit()
    print(response.text)
    logString = ("[Register]: User : " + str(message.author) + " has registered successfully with account : " + wowUsername + ".")
    print(logString)
    await send_message(logString, logsChannelID)
    await message.author.send("[Register]: Account has been successfully made.")
    
# account reset password function
async def accountmgr_password(message):
    # account set password $newpassword $newpassword
    messageParameters = message.content.split(" ")
    print("resetting password")
    
    if len(messageParameters) != 5:
        logString = ("[Account Management]: User : " + str(message.author) + " failed to CHANGE PASSWORD with following input : " + messageParameters[0] + " " + messageParameters[1] + " " + messageParameters[2] + " <REDACTED>.")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nPlease input `account set password <newPassword> <newPassword>`.\nExample: `account set password 123 123` would change any password associated with your discord to '123'.")
        return
    # does $newpassword = $newpassword?
    newPass = messageParameters[3]
    newPass_confirm = messageParameters[4]
    if newPass != newPass_confirm:
        logString = ("[Account Management]: User : " + str(message.author) + " failed to CHANGE PASSWORD. Variables `$newpassword` and `$newpassword` do not match.")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nPlease input `account set password <newPassword> <newPassword>`.\nExample: `account set password 123 123` would change any password associated with your discord to '123'.")
        return
    
    discordid = str(message.author.id).upper() # Does this discord user have an account?
    connection = mysql.connector.connect(user=mysqlUser, password=mysqlPass, host=mysqlHost, database=mysqlauthDB, port=mysqlPort) # db connection
    cursor = connection.cursor() # our cursor that selects n stuff
    registrationSQL = "SELECT username, email FROM account WHERE email = %s" # check if email(discordid) exists
    checkval = [
    discordid,
    ]
    cursor.execute(registrationSQL,checkval)
    result = cursor.fetchall()
    connection.commit() # We need this or the script will cache the query.
    if len(result) == 0: # if 0, then no accounts are associated with discordid
        logString = ("[Account Management]: User : " + str(message.author) + " failed to CHANGE PASSWORD. No email associated with the DiscordID : " + discordid + ".")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nNo account associated with your discord exists.")        
        return
    # perform SOAP command to reset password
    account = result[0][0]
    soap_url = "http://" + soapUser + ":"  + soapPass + "@" + soapHost + ":" + soapPort + "/"
    concat_string = "account set password " + account + " " + newPass + " " + newPass_confirm
    payload = """<SOAP-ENV:Envelope  
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
    xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/1999/XMLSchema" 
    xmlns:ns1="urn:AC">
    <SOAP-ENV:Body>
	<ns1:executeCommand>
	    <command>""" + concat_string + """</command>
	</ns1:executeCommand>
    </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>"""
    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }
    # POST request
    response = requests.request("POST", soap_url, headers=headers, data=payload)
    print(response.text)
    logString = ("[Account Management]: User : " + str(message.author) + " has successfully performed CHANGE PASSWORD with account : " + account + ".")
    print(logString)
    await send_message(logString, logsChannelID)
    await message.author.send("[Account Management]: Password has been successfully reset.")    
    return

# give GM powers if user has proper role in server
async def accountmgr_givepowers(message):
    guild = client.get_guild(discordServerID)
    discordid = int(message.author.id)
    server_member = guild.get_member(discordid)
    if not server_member.get_role(int(staffRoleID)):
        logString = ("[Account Management]: User : " + str(message.author) + " failed to GIVEMEPOWERS. User DiscordID : " + discordid + " does not have the required role : "  + staffRoleID + ".")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nYou do not have the powers to do this.")        
        return
    
    connection = mysql.connector.connect(user=mysqlUser, password=mysqlPass, host=mysqlHost, database=mysqlauthDB, port=mysqlPort) # db connection
    cursor = connection.cursor() # our cursor that selects n stuff
    registrationSQL = "SELECT username, email FROM account WHERE email = %s" # check if email(discordid) exists
    checkval = [
    discordid,
    ]
    cursor.execute(registrationSQL,checkval)
    result = cursor.fetchall()
    connection.commit() # We need this or the script will cache the query.
    if len(result) == 0: # if 0, then no accounts are associated with discordid
        logString = ("[Account Management]: User : " + str(message.author) + " failed to GIVEMEPOWERS. No email associated with the DiscordID : " + discordid + ".")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nNo account associated with your discord exists.")        
        return    
    
    # perform SOAP command to set RBAC
    account = result[0][0]
    soap_url = "http://" + soapUser + ":"  + soapPass + "@" + soapHost + ":" + soapPort + "/"
    concat_string = "account set gmlevel " + account + " " + soapRBAC + " -1"
    payload = """<SOAP-ENV:Envelope  
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
    xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/1999/XMLSchema" 
    xmlns:ns1="urn:AC">
    <SOAP-ENV:Body>
	<ns1:executeCommand>
	    <command>""" + concat_string + """</command>
	</ns1:executeCommand>
    </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>"""
    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }
    # POST request
    response = requests.request("POST", soap_url, headers=headers, data=payload)
#    print(response.text)
    logString = ("[Account Management]: User : " + str(message.author) + " has successfully performed GIVEMEPOWERS with account : " + account + ".")
    print(logString)
    await send_message(logString, logsChannelID)
    await message.author.send("[Account Management]: Account level changed.")    
    return

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # is message a DM, starts with "register ", and is not bot
    # syntax: register <username> <password>
    if str(message.channel).find("Direct Message") == -1:
        return

    if message.author.bot == True:
        return

    guild = client.get_guild(discordServerID)
    discordid = int(message.author.id)
    server_member = guild.get_member(discordid)
    if server_member == None:
        logString = ("[Account Management]: User : " + str(message.author) + " tried to input Command : '" + message + "' but is not in the Discord.")
        print(logString)
        await send_message(logString, logsChannelID)
        await message.author.send("[Account Management]: There was an error processing your command.\nYou are not in the Discord server.")        
        return
    
    if message.content.startswith('register'):
        await register(message)
        return
    
    if message.content.startswith('account set password'):
        await accountmgr_password(message)
        return
        
    if message.content.startswith('givemepowers'):
        await accountmgr_givepowers(message)
        return
client.run(config['discord']['apiKey'])