from slack import WebClient, RTMClient
import datetime

def periodic_ping_callback(rtmclient, client, usersList, arrayMods):
    timestampNeededEnd = datetime.datetime.now() - datetime.timedelta(days=7)
    timestampNeededStart = datetime.datetime.now() - datetime.timedelta(hours=4)
    response = client.conversations_history(channel="CAZN8J078",
                                            oldest=timestampNeededEnd.timestamp(),
                                            latest=timestampNeededStart.timestamp())#ID for #bottest
    cry = False
    listUsersToWelcome = []
    for message in response['messages']:
        # print(message["text"])
        if "reactions" not in message.keys():
           cry = True
           nameUserToWelcome = message["text"].split(" ")[0]
           nameUserToWelcome = nameUserToWelcome.split("|")[1]
           nameUserToWelcome = nameUserToWelcome[:-1]
           listUsersToWelcome.append(nameUserToWelcome)
        else:
            noValableReactions = True
            for reaction in message["reactions"]:
                if reaction['name'] in ['heavy_check_mark', 'watch', 'x']:
                    noValableReactions = False
                else:
                    pass
            if noValableReactions:
                cry = True
    if cry:
        hour = datetime.datetime.now().minute
        personToPing = arrayMods[hour]
        if personToPing is None:
            response = client.chat_postMessage(
                       channel='#bottest',
                       link_names=1,
                       text="There are unwelcomed users, but there is no mod to ping in the schedule. Please fix that as soon as possible.",
                       as_user=True)
            response = client.chat_postMessage(
                       channel='#bottest',
                       link_names=1,
                       text="List of unwelcomed users: "+str(listUsersToWelcome),
                       as_user=True)
        else:
            idModToPing = ''
            for (key, user) in usersList.items():
                if user == personToPing:
                    idModToPing = key
            response = client.chat_postMessage(
                       channel='#bottest',
                       link_names=1,
                       text="<@"+idModToPing+"> there are unwelcomed users after 4 hours. Please fix that as soon as possible.",
                       as_user=True)
            response = client.chat_postMessage(
                       channel='#bottest',
                       link_names=1,
                       text="List of unwelcomed users: "+str(listUsersToWelcome),
                       as_user=True)
    else:
        response = client.chat_postMessage(
                   channel='#bottest',
                   text="All users have been welcomed. Good.",
                   as_user=True)
    print("Trigger time:" + str(datetime.datetime.now()))