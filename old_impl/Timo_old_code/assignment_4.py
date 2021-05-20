import spacy
import requests

url = 'https://query.wikidata.org/sparql'

def get_search_id(word):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities', 
                  'language':'en',
                  'format':'json'}
    params['search'] = word


    json = requests.get(url,params).json()
    result_list = json['search'][0:3]
    search_id = [result['id'] for result in result_list]
    return search_id


def get_property_id(word):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities',
                  'type': 'property',
                  'language':'en',
                  'format':'json'}
    params['search'] = word
    json = requests.get(url,params).json()
    result_list = json['search'][0:3]
    property_id = [result['id'] for result in result_list]
    return property_id

def get_search(parse):
    search_id = ''
    simple_questions = ['What', 'Who', 'Where']
    if parse[1].lemma_ == 'be' and parse[0].text in simple_questions:
        if len(parse.ents) != 0:
            for ent in parse.ents : 
                search_id = get_search_id(ent.text)
        else:
            for word in parse[1:]:
                if word.text.istitle():
                    search_id = get_search_id(word.text)
    else:
        for word in parse:
            if word.dep_ in ['nsubj', 'dobj', 'pobj', 'nsubjpass'] and word.pos_ not in ['PRON']:
                search = phrase(word)
                print("Entity: ", search)
                search_id = get_search_id(search)
    return search_id

def get_property(parse):
    property_id = ""
    for word in parse:
        if word.pos_ == 'NOUN':
            print("property: ", word.text)
            just_property = word.lemma_
            property_id = get_property_id(just_property)
            break
        if word.dep_ == 'ROOT' and word.pos_ == 'VERB':
            print("property: ", word.text)
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
                for var in item :
                    print('{}\t{}'.format(var,item[var]['value']))
            return


def phrase(word) :
    children = []
    for child in word.subtree :
        children.append(child.text)
    return " ".join(children)

        
def main():
    
    
    nlp = spacy.load("en_core_web_sm") # this loads the model for analysing English text
    question = input('Please ask a question\n')
    parse = nlp(question) # parse the input 
    search_id = get_search(parse)
    property_id = get_property(parse)
 
    if property_id == '':
        print('no property found')
    else:
        if search_id == '':
            print('no entity found')
        else:
            print('search_id:', search_id)
            print('property_id:', property_id)
            query_list = make_queries(search_id, property_id)
            test_query(query_list)
                

main()

# This script can now answer (some) questions that start with 'who' and questions that 

# Questions that work:
# 1. When was Tom Hanks born? 
# 2. Who composed the music for Dunkirk?
# 3. Who directed Hellboy? 
# 4. Who created star wars?
# 5. When was the première of Iron Man?
# 6. Who wrote Titanic? 
# 7. Who narrated The Big Lebowski? 
# 8. Who owns Pixar? 
# 9. Who played Katniss Everdeen?
# 10. Who produced Interstellar? 
