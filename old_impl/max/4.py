import spacy
import requests


# create query for the entity and property for X of Y questions
def create_query(ent, pro):
    q = '''SELECT ?answerLabel 
                        WHERE {
                            wd:''' + ent + ''' p:''' + pro + ''' ?item.    #select property of the entity
                            ?item ps:''' + pro + ''' ?answer .         #select value of the property
                            #include the labels
                        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
                    }
        '''
    return q


# query for counting amount of property from entity for how many questions
def create_query_how(ent, prop):
    q = '''SELECT ?count
                   WHERE {
                   {
                       SELECT (COUNT(?item) AS ?count)       # count the amount of properties from the entity
                           WHERE{
                               wd:''' + ent + ''' wdt:''' + prop + ''' ?item   
                           }
                   }
                       SERVICE wikibase:label {               
                       # ... include the labels
                       bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
                       }
                   }
          '''

    return q


# query for 'which entity has property of kind attribute'
def create_query_which(ent, pro, attr):
    q = ''' SELECT DISTINCT ?item ?itemLabel
                WHERE {
                    ?item wdt:P106/wdt:P279* wd:''' + ent + ''' ;   # Items with the Occupation(P106) of the ent or
                                                                      # a subclass(P279)
                        p:''' + pro + ''' ?convictStat .               # ... with the property statement          
                    ?convictStat ps:''' + pro + ''' ?crime .           
                    ?crime wdt:P279* wd:''' + attr + ''' .           # Which is a subclass of(P279) the attribute
                    SERVICE wikibase:label {               
                    # ... include the labels
                    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
                    }
                }
       '''
    return q


# function that tokenizes the question
def query_execution(que):
    url_sparql = "https://query.wikidata.org/sparql"
    data = requests.get(url_sparql, params={"query": que, "format": "json"}).json()

    # if no results found, then return 0
    if not data["results"]["bindings"]:
        return 0

    return data


# functions that searches for the entity in a sentence
def search_entity(sentence):
    # variable to save entity in and check for sentence's length
    en = ''
    length_sentence = len(sentence)

    # check whether the entity is a movie
    for idx, token in enumerate(sentence):
        # check whether the word has an uppercase and is not the first word
        if sentence[idx + 1].text.istitle() and idx is not 0:
            while idx < length_sentence - 2:  # - 2 to ignore "?" at the end of the sentence
                idx = idx + 1
                if not sentence[idx].text.istitle():
                    continue
                en = en + " " + str(sentence[idx])  # save movie title in the variable
        # if a value for an entity is found, break the loop
        if en:
            break

    # remove quotation marks from the entity if they are present
    en = en.strip('"')

    return en


def search_property(sentence):
    # start by index 3 because property always starts at index 3 in this assignment
    idx = 3
    property_entity = ""

    for idx, token in enumerate(sentence):
        if token.text == "of":  # check whether the word 'of' is found of the form X of Y
            # check whether the part after the 'of' is followed by an uppercase, quotation marks or 'the'
            # because those indicate the start of the entity Y
            if sentence[idx + 1].text.istitle() or sentence[idx + 1].text == '"' or sentence[idx + 1].text == 'the':
                # save everything from index 3 till the word 'of' as property
                num = 3
                while num is not idx:
                    property_entity = property_entity + " " + str(sentence[num])
                    num = num + 1

                # if a property has been found, break the loop
                if property_entity:
                    break

    # remove quotation marks from property if present
    property_entity = property_entity.strip('"')
    # if property is in plural form, remove the s
    if property_entity[-1] == 's':
        property_entity = property_entity[:-1]

    return property_entity


# function that finds subjects using the dependency properties
def search_entity_dependency(text):
    subject = ""
    for w in text:
        if w.dep_ == "nsubj":
            for d in w.subtree:
                if d.dep_ is "nsubj":
                    subject = subject + d.text + ""

    if not subject:
        for w in text:
            if w.dep_ == "nsubjpass":
                for d in w.subtree:
                    if d.dep_ is "nsubjpass":
                        subject = subject + d.text + ""

    # remove plural form
    if subject[-1] == 's':
        subject = subject[:-1]

    return subject


# search properties with dependency relation questions
# for how questions
def search_property_dependency_how(text):
    property_dep = ""
    for w in text:
        if w.dep_ == "dobj":
            for d in w.subtree:
                if d.dep_ is "dobj":
                    property_dep = property_dep + d.text + ""

    # remove plural form
    if property_dep[-1] == 's':
        property_dep = property_dep[:-1]

    return property_dep


# function to use dependency relations to find
# attribute of which questions
def search_attribute_dependency_which(text):
    attribute = ""
    for w in text:
        if w.dep_ == "pobj":
            for d in w.subtree:
                if d.dep_ == "pobj":
                    attribute = attribute + d.text + " "
                if d.dep_ == "compound":
                    attribute = attribute + d.text + " "

    return attribute


# function to use dependency relations to find
# property of which questions
def search_property_dependency_which(text):
    property_dep = ""
    for w in text:
        if w.dep_ == "ROOT":
            property_dep = property_dep + w.text + ""
    return property_dep


if __name__ == '__main__':
    # this loads the model for analysing English text
    nlp = spacy.load("en_core_web_sm")

    # ask question to the user and parse the input
    question = input('Please ask a question\n')
    parse = nlp(question)

    # for word in parse:  # iterate over the token objects
    #     print(word.lemma_, word.pos_, word.dep_, word.head.lemma_)

    # If an questions starts with "What" or "Who" it is of the form X of Y
    # thus use the following functions to find the entity properties
    # q_type parameters is used to remember which questions type is used
    q_type = 0
    entity = ""
    property = ""
    attribute = ""
    if parse[0].text == "What" or parse[0].text == "Who":
        # find the entity and the property of the sentence
        q_type = 1
        entity = search_entity(parse)
        property = search_property(parse)
    if parse[0].text == "Which" or parse[1].text == "which":
        q_type = 2
        entity = search_entity_dependency(parse)
        property = search_property_dependency_which(parse)
        attribute = search_attribute_dependency_which(parse)
    if parse[0].text == "How" and parse[1].text == "many":
        q_type = 3
        entity = search_entity(parse)
        property = search_property_dependency_how(parse)

    # get the api and create parameters for the entity and property
    url = 'https://www.wikidata.org/w/api.php'
    params_entity = {'action': 'wbsearchentities',
                     'language': 'en',
                     'format': 'json'}

    params_attribute = {'action': 'wbsearchentities',
                        'language': 'en',
                        'format': 'json'}

    params_property = {'action': 'wbsearchentities',
                       'type': 'property',
                       'language': 'en',
                       'format': 'json'}

    # assign an entity to the entity parameter and a property to property parameter
    params_entity['search'] = entity
    params_property['search'] = property

    # if there is an attribute (for "which" questions)
    # search the entity of it
    if attribute:
        params_attribute['search'] = attribute

    # search for the entity and property with the wikidata API
    json_entity = requests.get(url, params_entity).json()
    json_property = requests.get(url, params_property).json()
    json_attribute = ""

    # if there is an attribute (for "which" questions)
    # search the wikidata id's for it
    if attribute:
        json_attribute = requests.get(url, params_attribute).json()

    # print("wikidata says ", json_attribute)

    # go through the list of entities and properties
    query = ""
    answer = 0
    for entity in json_entity['search']:
        # if an answer is already found, do not continue with searching for it
        if answer is not 0:
            break

        for prop in json_property['search']:
            # select different query for different types of questions
            # q_type 1 is X of Y questions
            if q_type == 1:
                query = create_query(entity['id'], prop['id'])
            # q_type 2 is "Which entity has property with attribute" questions
            if q_type == 2:
                for attribute in json_attribute['search']:
                    query = create_query_which(entity['id'], prop['id'], attribute['id'])
                    if query:
                        break
            # q_type 3 is "How many properties does entity have"
            if q_type == 3:
                query = create_query_how(entity['id'], prop['id'])

            answer = query_execution(query)

            # if an answer has been found, iterate through the returned answer(s)
            # and print it out
            if answer is not 0:
                for item in answer["results"]["bindings"]:
                    for var in item:
                        print("{}\t{}".format(var, item[var]["value"]))
                break
