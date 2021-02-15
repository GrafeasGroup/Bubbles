from typing import Dict, List

from bubbles.config import users_list


def extract_author(message_data: List[Dict], good_reactions: List[str]) -> str:
    """
    Function that determines the user that has reacted to a new user message. The
    reaction list is stored in message_data["reactions"]
    Example of the retrieved reaction list:
        [{'name': 'think-rotate', 'users': ['U4QEPLK6D', 'UE3VDJ002', 'U7T7G5GT0', 
        'UK98SNKCK', 'U01AL41499D'], 'count': 5}, {'name': 'discord', 'users': 
        ['UE3VDJ002'], 'count': 1}, {'name': 'heavy_check_mark', 'users': 
        ['UEEMDNC0K'], 'count': 1}]
    
    good_reactions is a list containing the names of the reactions to test.
    
    If message["reactions"] does not exist (or if message["reactions"] does not
    contain any of the good_reactions reactions), then the output is "Nobody". 
    If only one person has reacted with only one of the good_reactions reactions,
    then the function returns the name stored in the 'users' key. Otherwise, the
    function returns "Conflict".
    
    OVERRIDE CASES: the function will return "Abandoned" if :x: is stored as reaction,
    and "Banned" if :banhammer: is stored as reaction.
    """
    if "reactions" not in message_data.keys():
        return "Nobody"

    stored_results = {}
    for reaction in good_reactions:
        stored_results[reaction] = 0

    for reaction in message_data["reactions"]:
        if reaction["name"] == "x":
            return "Abandoned"
        if reaction["name"] == "banhammer":
            return "Banned"
        if reaction["name"] not in good_reactions:
            continue
        stored_results[reaction["name"]] = reaction["count"]
    if sum(stored_results.values()) > 1:
        return "Conflict"
    elif sum(stored_results.values()) == 0:
        return "Nobody"

    # Extraction of the good reaction used
    reaction_used = ""
    for name_reaction, number in stored_results.items():
        if number:
            reaction_used = name_reaction

    # Extraction of the author of the good reaction used
    for reaction in message_data["reactions"]:
        if reaction["name"] != reaction_used:
            continue
        result = reaction["users"][0]
    return users_list[result]
