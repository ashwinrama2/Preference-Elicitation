import json
import os
from random import shuffle, seed
import itertools


def elicit_human_preferences():

    user = os.getenv('USER') #identify user
    seed(hash(user)) #initialize random seed
    root = "/global/cfs/cdirs/nstaff/chatbot/preferences"

    #create file to store preference data
    os.makedirs(f'{root}/human_preference_data', exist_ok=True)
    target_data_file = f'{root}/human_preference_data/{user}.json'

    #initialize the contest preference data
    if os.path.isfile(target_data_file): #if the file exists, then load answered preferences
        contest_data = read_json_to_list(target_data_file)
    else: #if the file does not exist, the set up preference data
        contest_data = []
        write_list_to_json(contest_data, target_data_file)

    #the number of contests for which a preference was given
    num_contests_answered = len(contest_data)//2

    #print instructions
    os.system("clear")
    os.system("clear")
    print("""
    Thank you for contributing to the NERSC Chatbot Alignment Project!

    INSTRUCTIONS:
    * You'll see responses to NERSC-related questions from 2 random chatbots.
    * Indicate which response you prefer, or select 'no preference' if applicable.
    * There are 900 possible contests, but you can provide as many or as few preferences as you like.
    * NOTE: You may see the same question multiple times, but the chatbot responses will be different.
    * You can exit and resume anytime by re-launching the program ('python3 get_prefs.py').
    """)

    #confirm starting from user
    start = input("    Are you ready to proceed? [Y/N]: ")
    if start not in ["Y", "y", ""]:
        print("\nTerminating Process.\n")
        return

    #load the generated answers for each chatbot, and map them to the corresponding chatbot
    chatbots = ["Vicuna", "Mistral", "Zephyr", "OpenChat", "Snorkel", "Llama3", "Starling", "StarlingCode", "Gemma", "Qwen"]
    chatbots_dict = {chatbot:read_json_to_dict(f'{root}/test_answers/{chatbot}_answers.json') for chatbot in chatbots}

    #load the test questions into a dictionary
    test_questions_dict = read_json_to_dict(f'{root}/test_questions.json')

    #load the preference prompt .md file for the human
    eval_prompt = load_markdown(f'{root}/preference_prompt_human.md')

    #obtain list of all possible contests
    all_contests = generate_perms(chatbots, len(test_questions_dict))

    #cycle through iterator to elicit preferences
    for a, b, idx in all_contests:

        #if preference has already been given for this contest or the converse, then skip.
        if {"first":a, "second":b, "question":idx, "winner":a} in contest_data or {"first":a, "second":b, "question":idx, "winner":b} in contest_data or {"first":b, "second":a, "question":idx, "winner":a} in contest_data or {"first":b, "second":a, "question":idx, "winner":b} in contest_data:
            pass

        else:
            question = remove_after_last_period(test_questions_dict[idx])
            response1  = remove_after_last_period(chatbots_dict[a].get(idx, "No answer."))
            response2  = remove_after_last_period(chatbots_dict[b].get(idx, "No answer."))

            if response1 == "No answer." or response2 == "No answer.": #skip this preference contest, but still increment question counter
                pass

            else: #ask human for the preference
                os.system("clear")
                os.system("clear")
                print(eval_prompt.format(NUM=num_contests_answered+1, QUESTION=question, RESPONSE1=response1, RESPONSE2=response2))

                #ask user for preference, ensuring valid input
                print("Enter (without quotes) '1' for response #1, '2' for response #2, '0' for no preference, or 'E' to exit.")
                pref = input("Preference: ")
                print()
                while pref not in ["1", "2", "0", "e", "E"]:
                    print("*Invalid preference* Please only enter (without quotes) '1' for response #1, '2' for response #2, '0' for no preference, or 'E' to exit.")
                    pref = input("Preference: ")
                    print()

                #append preference to contest data
                if pref == "1":
                    contest_data.append({"first":a, "second":b, "question":idx, "winner": a})
                    contest_data.append({"first":b, "second":a, "question":idx, "winner": a})
                elif pref == "2":
                    contest_data.append({"first":a, "second":b, "question":idx, "winner": b})
                    contest_data.append({"first":b, "second":a, "question":idx, "winner": b})
                elif pref == "0":
                    contest_data.append({"first":a, "second":b, "question":idx, "winner": a})
                    contest_data.append({"first":b, "second":a, "question":idx, "winner": b})
                elif pref == "E" or pref == "e":
                    print("\nTerminating Process.\n")
                    return

                write_list_to_json(contest_data, target_data_file)
            
            num_contests_answered += 1

    print("\nCompleted All Pairwise Contests.\n")


def read_json_to_dict(filename):
    with open(filename, 'r') as file:
        content = file.read()   
        if not content.strip():  # If the file is empty, load an empty dictionary
            return {}
        else:  # Otherwise, load the JSON into a dictionary
            content = json.loads(content)
            return {int(key): value for key, value in content.items()}



def generate_perms(contestants, venues):
    contestant_pairs = itertools.permutations(contestants, 2)
    perms = [(c1, c2, v) for (c1, c2) in contestant_pairs for v in range(1, venues+1)]
    shuffle(perms)
    return perms


def read_json_to_list(filename):
    def convert_types(item):
        item["first"] = str(item["first"])
        item["second"] = str(item["second"])
        item["question"] = int(item["question"])
        item["winner"] = str(item["winner"])
        return item
    
    with open(filename, 'r') as file:
        content = file.read()
        if not content.strip():  # If the file is empty, load an empty list
            return []
        else:  # Otherwise, load the JSON into a list of dictionaries
            content = json.loads(content)
            return [convert_types(item) for item in content]


def write_list_to_json(lst, filename):
    with open(filename, 'w') as file:
        json.dump(lst, file, indent=4)


def load_markdown(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def remove_after_last_period(text):
    reference_index = text.rfind("References:")
    if reference_index == -1:
        return text
    last_period_index = text[:reference_index].rfind(".")
    if last_period_index == -1:
        return text
    return text[:last_period_index + 1]


if __name__ == '__main__':
    elicit_human_preferences()
