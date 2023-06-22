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
# IN WORLDSERVER.CONF, PLEASE SET SOAP.ENABLED = 1
soapHost = config['soap']['host']
soapUser = config['soap']['user'] # User, pass is the user/pass of an account that can access the console/in-game and create/set passwords, accounts, etc.
soapPass = config['soap']['pass']
soapPort = config['soap']['port']
## End Setup

client = discord.Client(intents=discord.Intents.default())

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
    print(message)
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
    
    if message.content.startswith('register '):
        await register(message)
        return
    
    if message.content.startswith('account set password '):
        await accountmgr_password(message)
        return
client.run(config['discord']['apiKey'])