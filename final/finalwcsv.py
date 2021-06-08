import os
import spacy
import requests
import time

# load the language model for English
nlp = spacy.load("en_core_web_sm")

# save the wikidata url
search_url = 'https://www.wikidata.org/w/api.php'

# save the query url
query_url = 'https://query.wikidata.org/sparql'

# search params for finding entities
search_params = {
    'action': 'wbsearchentities',
    'language': 'en',
    'format': 'json',
}

# use format json
query_params = {
    'format': 'json',
}

# standard query format
query_template = """
SELECT ?ansLabel
WHERE {{
        wd:{} wdt:{} ?ans.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}"""

# query for how many questions
query_how = '''SELECT ?count
                   WHERE {{
                   {{
                       SELECT (COUNT(?item) AS ?count)       # count the amount of properties from the entity
                           WHERE{{
                               wd:{} wdt:{} ?item
                           }}
                   }}
                       SERVICE wikibase:label {{
                       # ... include the labels
                       bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
                       }}
                   }}
          '''


# function that phrases the word to find the Entity
def phrase(word):
    children = []
    for child in word.subtree:
        if child.text.istitle():
            children.append(child.text)
    return " ".join(children)


# This function determines what the property of the sentence is
# by using the property translator: if root doesn't return anything
# then the function tries obj to see if that returns anything
# else None is returned
def basic_sub_obj(root, sub, obj):
    try:
        prop = property_translator[root.text]
        idx = obj_or_sub[prop]
    except KeyError:
        try:
            prop = property_translator[obj]
            idx = obj_or_sub[prop]
        except KeyError:
            return None, None
    return prop, sub if idx == 0 else obj


# results are printed
def print_results(data: dict):
    try:
        for item in data['results']['bindings']:
            for var in item:
                print(item[var]['value'])
        print("==========")
    except TypeError:
        print(data)
        print("==========")

# function transforms a variable to a string
def make_string(tokens):
    return " ".join([tok.text for tok in tokens]).rstrip()


# parsing old type of questions in the form of 'of'
def parse_name(tokens: dict, break_tok):
    parsed_tokens = []
    while tokens[0].text == 'of' or tokens[0].text == 'the':
        tokens = tokens[1:]
    for (idx, token) in enumerate(tokens):
        if token.text == break_tok:
            return parsed_tokens, idx + 1
        if token.pos_ == 'PUNCT': continue
        parsed_tokens.append(token)
    return None


# X of Y is substracted from the sentence:
# X is prop and Y is subj
def trivial_question(tokens: list):
    prop, idx = parse_name(tokens[2:], 'of')
    subj, idx = parse_name(tokens[idx + 2:], '?')
    return prop, subj

# Property translator that translates different meanings to a specific property
property_translator = {
    'born': 'birth',
    'die': 'death',
    'directed': 'director',
    'direct': 'director',
    'played': 'performer',
    'performed': 'performer',
    'composed': 'composer',
    'created': 'creator',
    'wrote': 'screenwriter',
    'narrated': 'narrator',
    'owns': 'owned by',
    'produced': 'producer',
    'casted': 'cast',
    'released': 'publication date',
    'première': 'publication date',
    'actor': 'cast member',
    'about': 'main subject',
    'shot': 'country of origin',
    'cast': 'cast member',
    'members': 'cast member'
}

# checks whether the word is a obj or subj
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
    'publication date': 0,
    'cast': 0,
    'cast member': 0,
    'main subject': 0,
    'country of origin': 0,
}

# check whether the question is of type "how many"
def is_how_many(tokens):
    if tokens[0].text == "How" and tokens[1].text == "many":
        return True
    return False


# function that checks whether the sentence is in the form of X of Y
def is_trivial(tokens: list):
    fir = tokens[0].text
    if fir not in ["What", "Who", "When", "Who"]:
        return False
    if tokens[1].lemma_ != "be":
        return False
    if tokens[2].pos_ != "DET":
        return False
    for tok in tokens[2:]:
        if tok.text == 'of':
            return True
    return False


# function that returns 'date of' if a sentence starts with When
# or returns 'place of' if a sentence starts with Where
def when_where(tokens: list, root, sub, obj):
    prop, sub = basic_sub_obj(root, sub, obj)
    if prop == "publication date" or prop == "country of origin":
        return prop, sub
    return ("date of " + prop, sub) if tokens[0].text == "When" else (
        "place of " + prop, sub) if tokens[0].text == "Where" else (prop, sub)


# parser for yes/no question types
def parse_yes_no_question(question: str):
    type = 0
    tokens = nlp(question.strip())
    prop, sub, obj = find_sub_obj_prop_yes_no(tokens)
    print("sub: ", sub, ", obj: ", obj)
    return prop, sub, obj, type


# checks how to extract the property and subject from a sentence based on the question form
def parse_question(question: str):
    tokens = nlp(question.strip())
    for word in tokens:
        print(word.text, word.dep_, word.lemma_, word.pos_)
    type = 0
    if is_trivial(tokens):
        prop, sub = trivial_question(tokens)
        prop, sub = make_string(prop), make_string(sub)
    elif is_how_many(tokens):
        prop, sub = get_prop_sub(tokens[1:] if tokens[-1].text ==
                                   "." else tokens)
        type = 1
    else:
        root, sub, obj = find_sub_obj(tokens)
        prop, sub = when_where(tokens, root, sub, obj)
    print("Property: ", prop)
    print("Entity: ", sub)
    return prop, sub, type


# Find the object and subject of a sentence
# if the object wasn't found, try different lemma's to find it
def find_sub_obj(tokens: list):
    sentence = list(tokens.sents)[0]
    sub, obj = None, None
    for child in sentence.root.children:
        if child.dep_ == 'nsubj':
            sub = phrase(child)
            continue
        if child.dep_ == 'dobj':
            obj = phrase(child)
    if obj == None:
        for word in sentence:
            if word.pos_ == 'ADP':
                obj = word.text
            if word.pos_ == 'NOUN':
                obj = word.text
    return sentence.root, sub, obj


def find_sub_obj_prop_yes_no(tokens: list):
    sentence = list(tokens.sents)[0]
    sub, obj, property = None, None, None
    for child in sentence.root.children:
        if child.dep_ == 'nsubj':
            sub = phrase(child)
            continue
        if child.dep_ == 'dobj':
            obj = phrase(child)
            continue
        if child.dep_ == 'agent' or child.dep_ == 'prep':
            for grandchild in child.children:
                if grandchild.dep_ == 'pobj':
                    obj = phrase(grandchild)
    for word in tokens:
        if word.pos_ == 'NOUN':
            property = word.lemma_
            break
        if word.dep_ == 'ROOT' and word.pos_ == 'VERB':
            property = word.lemma_
            break

    if not property:
        check = None
        for word in tokens:
            if word.dep_ == 'nsubj':
                check = word.lemma_
            if word.dep_ != 'nsubj' and check != None:
                property = word.lemma_
                break

    return property, sub, obj


def get_prop_sub(tokens):
    property, subject = None, None

    # get subject of the sentence
    if len(tokens.ents) != 0:
        for ent in tokens.ents:
            subject = ent.text
    else:
        for word in tokens[1:]:
            if word.text.istitle() or word.pos_ == "NUM":
                subject = subject + word.text

    if subject is None:
        for word in tokens:
            if word.dep_ in ['nsubj', 'dobj', 'pobj', 'nsubjpass', 'nummod'
                             ] and word.pos_ not in ['PRON']:
                subject = phrase(word)

    # get property of the sentence
    for word in tokens:
        if word.pos_ == 'NOUN':
            property = word.lemma_
            break
        if word.dep_ == 'ROOT' and word.pos_ == 'VERB':
            property = word.lemma_
            break

    return property, subject


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
    res = requests.get(url, {**query_params, 'query': what})
    if res.status_code != 200:
        raise Exception('Received invalid status code {}: {}'.format(
            res.status_code, res.reason))
    return res.json()


# added a trivial retry policy when there is no results
def run_query(prop, subj, type):
    try:
        subjs = make_request(subj)['search']
        if len(subjs) > 3:
            subjs = subjs[:3]
        props = make_request(prop, True)['search']
        if len(props) > 3:
            props = props[:3]
        for x in range(len(subjs)):
            for y in range(len(props)):
                if type == 1:
                    query = query_how.format(subjs[x]['id'],
                                             props[y]['id'])
                    res = make_query(query)
                    if res['results']['bindings']:
                        return res
                else:
                    query = query_template.format(subjs[x]['id'],
                                                  props[y]['id'])
                    res = make_query(query)
                    if res['results']['bindings']:
                        return res
                time.sleep(1)
    except KeyError:
        return "ERROR"


url = 'https://query.wikidata.org/sparql'


def get_search_id(word):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    params['search'] = word

    json = requests.get(url, params).json()
    result_list = json['search'][0:3]
    search_id = [result['id'] for result in result_list]
    return search_id


def get_property_id(word):
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbsearchentities',
        'type': 'property',
        'language': 'en',
        'format': 'json'
    }
    params['search'] = word
    json = requests.get(url, params).json()
    result_list = json['search'][0:3]
    property_id = [result['id'] for result in result_list]
    return property_id


def get_search(parse):
    search_id = ''
    simple_questions = ['What', 'Who', 'Where']
    if parse[1].lemma_ == 'be' and parse[0].text in simple_questions:
        if len(parse.ents) != 0:
            for ent in parse.ents:
                search_id = get_search_id(ent.text)
        else:
            for word in parse[1:]:
                if word.text.istitle():
                    search_id = get_search_id(word.text)
    else:
        for word in parse:
            if word.dep_ in ['nsubj', 'dobj', 'pobj', 'nsubjpass', 'nummod'
                             ] and word.pos_ not in ['PRON']:
                search = phrase(word)
                search_id = get_search_id(search)
    return search_id


def get_property(parse):
    property_id = ""
    for word in parse:
        if word.pos_ == 'NOUN':
            just_property = word.lemma_
            property_id = get_property_id(just_property)
            break
        if word.dep_ == 'ROOT' and word.pos_ == 'VERB':
            property_id = get_property_id(word.lemma_)
            if property_id == "":
                property_id = get_property_id(word.text)
            break
    return property_id


def make_queries(search_id, property_id):
    query_list = []
    for search in search_id:
        for prop in property_id:

            query = 'SELECT ?itemLabel WHERE { wd:' + search + ' wdt:' + prop + '''?item.
SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}'''
            query_list.append(query)
    return query_list


def test_query(query_list):
    for x in query_list:
        data = requests.get(url, params={'query': x, 'format': 'json'}).json()
        if len(data['results']['bindings']) == 0:
            continue
        else:
            for item in data['results']['bindings']:
                for var in item:
                    print('{}'.format(item[var]['value']))
            return


def run_auxiliary(line):
    parse = nlp(line)  # parse the input
    search_id = get_search(parse)
    property_id = get_property(parse)
    if property_id and search_id:
        query_list = make_queries(search_id, property_id)
        test_query(query_list)
        return
    raise Exception("no results")

def read_csv(f):
    with open(f, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
        return [row[1] for row in reader]


def run_system(line):
    temp_tok = nlp(line)
    if temp_tok[0].text in ["Does", "Did",
                            "Is"]:  #yes/no question requires different output
        prop, sub, obj, type = parse_yes_no_question(line.strip())

        print(prop, sub, obj)  #check prop sub and obj
        res_list = run_query(prop, sub if temp_tok[0].text == "Is" else obj,
                               type)
        check = obj if temp_tok[0].text == "Is" else sub
        try:

            yes_no = False
            for item in res_list['results']['bindings']:
                for var in item:
                    if item[var]['value'] == check:
                        yes_no = True
            return "Yes" if yes_no else "No"
        except TypeError:
            print("TypeError\nResults: {}\nCheck {}\n".format(res_list, check))

    else:
        prop, sub, type = parse_question(line.strip())
        return run_query(prop, sub, type)


def run(line):
    res = None
    try:
        res = run_system(line)
    except Exception as e:
        print("DEBUG: {}".format(e))  # remove before submission
    finally:
        if res == None or res == "ERROR":
            time.sleep(1)
            try:
                run_auxiliary(line)
            except Exception as e:
                print("DEBUG: {}".format(e))  # remove before submission
                print("No results found")
            return
        else:
            print_results(res)


if __name__ == '__main__':
    line = input("1 Ask a question\n2 insert a path to a csv file:\n").strip()


    _, ext = os.path.splitext(line)
    if ext == '.csv':
        qs = read_csv(line)
        for x in qs:
            print(
                "========\nthe question that is being tested is: {}\nthe answer is"
                .format(x))
            run(x)
    else:
        run(line)

# working
# 2 3 4 7 9 10
# missing
# 1 5 6 8

# the 8 the problem is recognizing 12 angry men. Basically the problem
# is that when we call phrase angry men is not recognized as a
# title.