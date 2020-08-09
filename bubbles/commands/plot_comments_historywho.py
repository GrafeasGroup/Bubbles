from slack import WebClient, RTMClient
import datetime
from numpy import zeros, arange, shape, flip
import matplotlib.pyplot as plt
import matplotlib

def plot_comments_historywho_command(rtmclient, client, usersList):
    #lastDatetime = datetime.datetime(2018, 5, 30).timestamp() # First post on 30/05/2018
    lastDatetime = datetime.datetime.now().timestamp()
    countReactionsAll = {}
    countReactionsPeople = {}
    datetimeNow = datetime.datetime.now()
    response = client.conversations_history(channel="CAZN8J078",
                                            latest=lastDatetime,
                                            limit=100)#ID for #bottest
    # countReactions['Nobody'] = 0
    idUserToCheck = usersList["Patrick Fagan"]
    for message in response['messages']:
        
        timeSend = datetime.datetime.fromtimestamp(float(message["ts"]))
        differenceDatetime = datetimeNow - timeSend
        differenceDays = differenceDatetime.days
        if "reactions" not in message.keys():
            if 'Nobody' not in countReactionsPeople.keys():
                countReactionsPeople['Nobody'] = {}
            if differenceDays not in countReactionsPeople['Nobody'].keys():
                countReactionsPeople['Nobody'][differenceDays] = 0
            countReactionsPeople['Nobody'][differenceDays] = countReactionsPeople['Nobody'][differenceDays] + 1
        else:
            noValableReaction = True
            for reaction in message["reactions"]:
                # Ignore all reactions unrelated to welcoming people
                if reaction['name'] not in ['heavy_check_mark']: #, 'watch']:
                    pass
                else:
                    if reaction["count"] > 1: # Several people have reacted to the same message
                        if 'Conflict' not in countReactionsPeople.keys():
                            countReactionsPeople['Conflict'] = {}
                        if differenceDays not in countReactionsPeople['Conflict'].keys():
                            countReactionsPeople['Conflict'][differenceDays] = 0
                        noValableReaction = False
                        countReactionsPeople['Conflict'][differenceDays] = countReactionsPeople['Conflict'][differenceDays] + 1
                    else: # only one person has reacted to the message
                        userWhoHasReacted = reaction["users"][0]
                        #print(reaction["users"])
                        nameUserWhoHasReacted = usersList[userWhoHasReacted]
                        #print(nameUserWhoHasReacted)
                        if nameUserWhoHasReacted != "Patrick Fagan":
                            if "Other" not in countReactionsPeople.keys():
                                countReactionsPeople["Other"] = {}
                            if differenceDays not in countReactionsPeople["Other"].keys():
                                countReactionsPeople["Other"][differenceDays] = 0
                                countReactionsPeople["Other"][differenceDays] = countReactionsPeople["Other"][differenceDays] + 1
                        else:
                            if "Patrick Fagan" not in countReactionsPeople.keys():
                                countReactionsPeople["Patrick Fagan"] = {}
                            if differenceDays not in countReactionsPeople["Patrick Fagan"].keys():
                                countReactionsPeople["Patrick Fagan"][differenceDays] = 0
                                countReactionsPeople["Patrick Fagan"][differenceDays] = countReactionsPeople["Patrick Fagan"][differenceDays] + 1
                        noValableReaction = False
                            
            if noValableReaction:
                if 'Nobody' not in countReactionsPeople.keys():
                    countReactionsPeople['Nobody'] = {}
                if differenceDays not in countReactionsPeople['Nobody'].keys():
                    countReactionsPeople['Nobody'][differenceDays] = 0
                countReactionsPeople['Nobody'][differenceDays] = countReactionsPeople['Nobody'][differenceDays] + 1
                    
        timeSend = datetime.datetime.fromtimestamp(float(message["ts"]))
        differenceDatetime = datetimeNow - timeSend
        differenceDays = differenceDatetime.days
        if differenceDays not in countReactionsAll.keys():
            countReactionsAll[differenceDays] = 0
        countReactionsAll[differenceDays] = countReactionsAll[differenceDays] + 1
        # print(str(timeSend)+"| "+userWhoSentMessage+" sent: "+textMessage)
        lastDatetime = timeSend.timestamp()
        #print(str(lastDatetime))
        #print(timeSend)
    response = client.chat_postMessage(
                           channel='#bottest',
                           text=str(len(response['messages']))+" messages retrieved since "+str(timeSend),
                           as_user=True)
    numberPosts = {}
    #print(countReactions.keys())
    dates = []
    legends = []
    maxDay = -1
    for name in countReactionsPeople.keys():
        maxDay = max(maxDay, max(countReactionsPeople[name].keys()))
        legends.append(name)
    postsHist = zeros((maxDay+1, len(countReactionsPeople.keys())))
    indiceUser = 0
    cmap = [matplotlib.cm.get_cmap('jet'), matplotlib.cm.get_cmap('inferno'), matplotlib.cm.get_cmap('hsv')]
    for name in countReactionsPeople.keys():
        numberPosts[name] = []
        # dates[name] = []
        #print(countReactionsPeople[name])
        for i in range(0, max(countReactionsPeople[name].keys())):
            if i not in countReactionsPeople[name].keys():
                numberPosts[name].append(0)
            else:
                numberPosts[name].append(countReactionsPeople[name][i])
                postsHist[i][indiceUser] = countReactionsPeople[name][i]
        #print("Day "+str(i)+": "+str(numberPosts[-1]))
        indiceUser = indiceUser + 1
    for i in range(0, maxDay+1):
        differenceDays = datetime.timedelta(days=i)
        newDate = datetimeNow - differenceDays
        dates.append(newDate)
    bottoms = postsHist[:, 0] * 0
    datesNum = matplotlib.dates.date2num(dates)
    i = 0
    print(countReactionsPeople.keys())
    for name in countReactionsPeople.keys():
        cmapChosen = cmap[(int(i / 7))%3]
        colour = cmapChosen(float((i%7)/7))
        plt.bar(range(0, maxDay+1), postsHist[:, i], 1, bottom = bottoms, label=name, color=colour)
        bottoms = bottoms + postsHist[:, i]
        i = i+1
    print(shape(postsHist))
    print(maxDay)
    # plt.bar(postsHist, maxDay+1, stacked='True')
    plt.xlabel("Daydelta")
    plt.xlim(maxDay, 0)
    plt.ylabel("Number of new volunteers")
    plt.grid(True, 'both')
    plt.legend()
    plt.savefig("plotHourMods.png")
    response = client.files_upload(
           channels='#bottest',
           file="plotHourMods.png",
           title="Just vibing.",
           as_user=True)
