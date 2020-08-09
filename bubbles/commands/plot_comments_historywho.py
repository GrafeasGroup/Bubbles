from bubbles.config import client, rtm_client, PluginManager, DEFAULT_CHANNEL, users_list, rooms_list
from typing import Dict
import datetime
from numpy import zeros, shape, flip, cumsum
import matplotlib.pyplot as plt

def plot_comments_historywho_command(a, b, c, message_data: Dict) -> None:
    #lastDatetime = datetime.datetime(2018, 5, 30).timestamp() # First post on 30/05/2018
    lastDatetime = datetime.datetime.now().timestamp()
    countReactionsAll = {}
    countReactionsPeople = {}
    datetimeNow = datetime.datetime.now()
    
    if '"' not in message_data.get('text') and message_data.get('text') != "!historywho -h":
        response = client.chat_postMessage(
               channel=message_data.get("channel"),
               text='`historywho` requires that you surround the name of the person between `" "`!',
               as_user=True)
        return
    
    namePersonToSearch = message_data.get("text").split('"')[1]
    if namePersonToSearch not in users_list.keys():
        response = client.chat_postMessage(
               channel=message_data.get("channel"),
               text=f'ERROR! {namePersonToSearch} is not on the list of users.',
               as_user=True)
        return
        
    otherParams = message_data.get("text").split('"')[0]
    args = otherParams.split()
    number_posts = 100
    if len(args) == 2:
        if args[1] in ['-h', '--help', '-H', 'help']:
            response = client.chat_postMessage(
               channel=message_data.get("channel"),
               text='`!historywho [number of posts] "[person]"` shows the number of new volunteers welcomed by `person` in function of their day, comparing it to the other folks and non-welcomed volunteers. `number of posts` must be an integer between 1 and 1000 inclusive.',
               as_user=True)
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        response = client.chat_postMessage(
           channel=message_data.get("channel"),
           text='ERROR! Too many arguments given as inputs! Syntax: `!history [number of posts] "[person]`',
           as_user=True)
        return
    
    response = client.conversations_history(channel=rooms_list["new_volunteers"],
                                            latest=lastDatetime,
                                            limit=number_posts)#ID for #bottest
    # countReactions['Nobody'] = 0
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
                if reaction['name'] not in ['heavy_check_mark', 'watch']:
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
                        nameUserWhoHasReacted = users_list[userWhoHasReacted]
                        #print(nameUserWhoHasReacted)
                        if nameUserWhoHasReacted != namePersonToSearch:
                            if "Other" not in countReactionsPeople.keys():
                                countReactionsPeople["Other"] = {}
                            if differenceDays not in countReactionsPeople["Other"].keys():
                                countReactionsPeople["Other"][differenceDays] = 0
                                countReactionsPeople["Other"][differenceDays] = countReactionsPeople["Other"][differenceDays] + 1
                        else:
                            if namePersonToSearch not in countReactionsPeople.keys():
                                countReactionsPeople[namePersonToSearch] = {}
                            if differenceDays not in countReactionsPeople[namePersonToSearch].keys():
                                countReactionsPeople[namePersonToSearch][differenceDays] = 0
                            countReactionsPeople[namePersonToSearch][differenceDays] = countReactionsPeople[namePersonToSearch][differenceDays] + 1
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
                           channel=DEFAULT_CHANNEL,
                           text=f"{str(len(response['messages']))} messages retrieved since {str(timeSend)}",
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
    colours = ["#00FF00", "#FF0000", "#0000FF", "#808080"]
    for name in [namePersonToSearch, "Other", "Nobody", "Conflict"]:
        if name in countReactionsPeople.keys():
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
    for i in range(maxDay, -1, -1):
        differenceDays = datetime.timedelta(days=i)
        newDate = datetimeNow - differenceDays
        dates.append(newDate)
    i = 0
    print(countReactionsPeople.keys())
    for name in [namePersonToSearch, "Other", "Nobody", "Conflict"]:
        if name in countReactionsPeople.keys():
            plt.plot(dates, cumsum(flip(postsHist[:, i])), label=name, color=colours[i])
            i = i+1
    print(shape(postsHist))
    print(maxDay)
    # plt.bar(postsHist, maxDay+1, stacked='True')
    plt.xlabel("Day")
    plt.ylabel("Number of new volunteers")
    plt.grid(True, 'both')
    plt.legend()
    plt.savefig("plotHourMods.png")
    plt.close()
    response = client.files_upload(
           channels='#bottest',
           file="plotHourMods.png",
           title="Just vibing.",
           as_user=True)

PluginManager.register_plugin(plot_comments_historywho_command, r"historywho")