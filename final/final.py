import spacy
import requests

# globals
search_url = 'https://www.wikidata.org/w/api.php'

query_url = 'https://query.wikidata.org/sparql'

search_params = {
    'action': 'wbsearchentities',
    'language': 'en',
    'format': 'json',
}

query_params = {
    'format': 'json',
}

property_translator = {
    'born': 'birth',
    'die': 'death',
    'directed': 'director',
    'played': 'performer',
    'performed': 'performer',
    'composed': 'composer',
    'created': 'creator',
    'wrote': 'screenwriter',
    'narrated': 'narrator',
    'owns': 'owned by',
    'produced': 'producer',
    'casted': 'cast',
    'premiere': 'premierte',
}

obj_or_sub = {
    'birth': 0,
    'death': 0,
    'director': 1,
    'performer': 1,
    'composer': 1,
    'creator': 1,
    'screenwriter': 1,
    'narrator': 1,
    'owned by': 1,
    'producer': 1,
    'cast': 0,
}

query_template = """
SELECT ?ansLabel
WHERE {{
        wd:{} wdt:{} ?ans.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}"""

nlp = spacy.load("en_core_web_sm")


# burocracy
def make_request(what: str, is_prop=False, url=search_url):
    return requests.get(
        url, {
            **({
                'type': 'property'
            } if is_prop else {}), 'search': what,
            **search_params
        }).json()


def make_query(what: str, url=query_url):
    return requests.get(url, {**query_params, 'query': what}).json()


def make_string(tokens):
    return " ".join([tok.text for tok in tokens]).rstrip()


# parsing old type of questions
def parse_name(tokens: dict, break_tok):
    parsed_tokens = []
    while (tokens[0].text == 'of' or tokens[0].text == 'the'):
        tokens = tokens[1:]
    for (idx, token) in enumerate(tokens):
        if token.text == break_tok:
            return parsed_tokens, idx + 1
        if token.pos_ == 'PUNCT': continue
        parsed_tokens.append(token)
    return None


def trivial_question(tokens: list):
    prop, idx = parse_name(tokens[2:], 'of')
    subj, idx = parse_name(tokens[idx + 2:], '?')
    return prop, subj


def is_trivial(tokens: list):
    fir = tokens[0].text
    # sec = tokens[1].text
    # third = tokens[2].text
    if fir not in ["What", "Who", "When"]:
        return False
    if tokens[1].lemma_ != "be":
        return False
    # if sec not in ["is", "was", "were", "are"]:
    #     return False
    if tokens[2].pos_ != "DET":
        return False
    # if third not in ["the", "a", "an"]:
    #     return False
    for tok in tokens[2:]:
        if tok.text == 'of':
            return True
    return False


# parsing new type of questions


def phrase(word):
    children = []
    for child in word.subtree:
        if child.text.istitle():
            children.append(child.text)
    return " ".join(children)


def find_sub_obj(tokens: list):
    sentence = list(tokens.sents)[0]
    sub, obj = None, None
    for child in sentence.root.children:
        if child.dep_ == 'nsubj':
            sub = phrase(child)
            continue
        if child.dep_ == 'dobj':
            obj = phrase(child)
    return sentence.root, sub, obj


def basic_sub_obj(root, sub, obj):
    try:
        prop = property_translator[root.text]
        idx = obj_or_sub[prop]
    except KeyError:
        return None, None
    return prop, sub if idx == 0 else obj


def when_where(tokens: list, root, sub, obj):
    prop, sub = basic_sub_obj(root, sub, obj)
    return ("date of " + prop, sub) if tokens[0].text == "When" else (
        "place of " + prop, sub) if tokens[0].text == "Where" else (prop, sub)


def parse_question(question: str):
    tokens = nlp(question.strip())
    if is_trivial(tokens):
        prop, sub = trivial_question(tokens)
        prop, sub = make_string(prop), make_string(sub)
    else:
        root, sub, obj = find_sub_obj(tokens)
        prop, sub = when_where(tokens, root, sub, obj)
    return prop, sub


# added a trivial retry policy when there is no results
def run_query(prop, subj):
    subjs = make_request(subj)['search']
    if len(subjs) > 3:
        subjs = subjs[:3]
    props = make_request(prop, True)['search']
    if len(props) > 3:
        props = props[:3]
    for x in range(len(props)):
        for y in range(len(subjs)):
            query = query_template.format(subjs[y-1]['id'], props[x-1]['id'])
            res = make_query(query)
            if res['results']['bindings']:
                return res
    return {
        'results': {
            'bindings': ["No results found, try another question"]
        }
    }


def print_results(data: dict):
    for item in data['results']['bindings']:
        try:
            for var in item:
                print(item[var]['value'])
        except TypeError:
            print(item)
            


# old type of questions
q0 = "What is the duration of I Am Legend?"
q1 = "Who is the author of Lord of The Rings?"
q2 = "What are the main subject of Interstellar?"

# new type of questions
q3 = "When did Alan Rickman die?"
q4 = "Where was Morgan Freeman born?"
q5 = "When was Daniel Craig born?"
q6 = "Who directed The Shawshank Redemption?"
q7 = "Which actor played Aragorn in Lord of the Rings?"
q8 = "Which actors played James Bond?"
q9 = "Who directed Interstellar?"

# TO DO --> they work in other models
q10 = "When was the première of Iron Man?" # Timo's model
q11 = "Who are the voice actors for Adventure Time?" # Lennard's model
q12 = "Who designed the costumes for 'les intouchables'?" # Lennard's model
q13 = "Who dubbed the voices for Adventure Time?" # Lennard's model
q14 = "Who casted in Uncut Gems?" # Lennard's model
q15 = "What was Interstellar influenced by?" # Lennard's model
q16 = "How many children does Will Smith have?" # add query of Aylar's model "4.py"
q17 = "Which directors were convicted of a sex crime?" # add query of Aylar's model "4.py"

qs_old = [q0, q1, q2]
qs_sub_obj = [q3, q4, q5, q6, q7, q8, q9]

qs = [*qs_old, *qs_sub_obj]

# The types of questions covered beside the old type of question are:
# When, Where, Which. Moreover, the most important thing is that all
# these new type of questions are based on the fact that the property
# is expressed by the main verb of the sentence and in particular this
# system cover the verbs that are inside the variable
# property_translator. NOTE: it is therefore trivial to add new verbs
# to this variable, therefore the system can be easily enhanced.

if __name__ == '__main__':
    line = input(
        "Ask a question or type test for check all the example questions:\n")
    if line.strip() == "test":
        for x in qs:
            prop, sub = parse_question(x)
            print(
                "========\nthe question that is being tested is: {}\nthe answer is"
                .format(x))
            print_results(run_query(prop, sub))
    else:
        prop, sub = parse_question(line.strip())
        print("the answer is:")
        print_results(run_query(prop, sub))
