#!/usr/bin/env python
# coding: utf-8

# # Advanced Question Analysis
# 
# The goal of this assignment is to write a more flexible version of the interactive QA system. As in the previous assignment, the system should be able to take a question in natural language (English) as input, analyse the question, and generate a SPARQL query for it.
# 
# ## Assignment  // Additional requirements
# 
# * Make sure that your system can analyse at least two more question types. E.g. questions that start with *which*, *when*, where the property is expressed by a verb, etc.
# * Apart from the techniques introduced last week (matching tokens on the basis of their lemma or part-of-speech), also include at least one pattern where you use the dependency relations to find the relevant property or entity in the question. 
# * Include 10 examples of questions that your system can handle, and that illustrate the fact that you cover additional question types
# 
# ## Examples
# 
# Here is a non-representative list of questios and question types to consider. See the list with all questions for more examples
# 
# * For what movie did Leonardo DiCaprio win an Oscar?
# * How long is Pulp Fiction?
# * How many episodes does Twin Peaks have?
# * In what capital was the film The Fault in Our Stars, filmed?
# * In what year was The Matrix released?
# * When did Alan Rickman die?
# * Where was Morgan Freeman born?
# * Which actor played Aragorn in Lord of the Rings?
# * Which actors played the role of James Bond
# * Who directed The Shawshank Redemption?
# * Which movies are directed by Alice Wu?
# 

# In[1]:


import spacy

nlp = spacy.load("en_core_web_sm") # this loads the model for analysing English text
                   


# ## Dependency Analysis with Spacy
# 
# All the functionality of Spacy, as in the last assignment, is still available for doing question analysis. 
# 
# In addition, also use the dependency relations assigned by spacy. Note that a dependency relation is a directed, labeled, arc between two tokens in the input. In the example below, the system detects that *movie* is the subject of the passive sentence (with label nsubjpass), and that the head of which this subject is a dependent is the word *are* with lemma *be*. 
# 

# In[59]:


question = 'Who designed the costumes for the dark knight rises'

parse = nlp(question) # parse the input 

for word in parse : # iterate over the token objects 
    print(word.lemma_, word.pos_, word.dep_, word.head.lemma_)


# ## Phrases
# 
# You can also match with the full phrase that is the subject of the sentence, or any other dependency relation, using the subtree function 
# 

# In[82]:


def phrase(word) :
    children = []
    for child in word.subtree :
        children.append(child.text)
    return " ".join(children)
        
question = 'Who designed the costumes for The Dark Knight Rises?'

parse = nlp(question) # parse the input 

for word in parse:
    if word.dep_ == 'nsubj' or word.dep_ == 'agent' :
        phrase_text = phrase(word)
        print(phrase_text)
        


# ## Visualisation
# 
# For a quick understanding of what the parser does, and how it assigns part-of-speech, entities, etc. you can also visualise parse results. Below, the entity visualiser and parsing visualiser is demonstrated. 
# This code is for illustration only, it is not part of the assignment. 

# In[57]:


from spacy import displacy

question = "Who wrote the music for the dark knigt rises?"

parse = nlp(question)

displacy.render(parse, jupyter=True, style="ent")

displacy.render(parse, jupyter=True, style="dep")


# In[88]:


# imports
import spacy
import requests

# pre-inits
url = 'https://www.wikidata.org/w/api.php'

nlp = spacy.load("en_core_web_sm") # this loads the model for analysing English text

# input
question = input('Please ask a question\n')

# parse the input
parse = nlp(question)  

#determine type of question
questiontype = 0
idx=0
for word in parse:
    if str(word.pos_) == 'AUX':
        questiontype = 1
        #question has AUX verb -> X of Y? / X for Y? type questions
    if str(word.pos_) == 'VERB':
        questiontype = 2
        #question contains verb next to aux, verb dictates the property


#extract X based on question type
if questiontype == 1: #X of Y type question
    idx=0
    while(parse[idx].dep_ != 'ROOT'): #cycle through parse until root verb is found
        idx+=1
    idx+=1
    if(str(parse[idx]) == 'the'): #in case the sentence contains a 'the' before the X
        idx+=1
    prop_idx_start = idx
    while(str(parse[idx]) != 'of' and str(parse[idx]) != 'for'):
        idx+=1
    prop_idx_end = idx
    X = str(parse[prop_idx_start:prop_idx_end].lemma_)

if questiontype == 2: #Extract X from root verb
    for word in parse:
        if word.dep_ == 'ROOT':#use dependency to find root verb
            X = str(word.lemma_)
            for subword in parse: #for more complex properties
                if subword.dep_ == 'dobj' and subword.head.lemma_ == X:
                    X = str(subword.lemma_) + " " + X
            
# Find X from wikidata
params = {'action':'wbsearchentities', 
            'type':'property',
            'language':'en',
            'format':'json'
            }
params['search'] = X
json = requests.get(url,params).json()
prop = json['search'][0]['id']

idx = 0
#extract Y based on question type
if questiontype == 1: #X of Y type question
    while(str(parse[idx]) != 'of' and str(parse[idx]) != 'for'):
        idx+=1
    idx+=1
    Y = ''#empty string to init
    #get rid of punctuation around movie title
    while(idx<len(parse)):
        if(parse[idx].pos_ != 'PUNCT'):
            Y = Y + str(parse[idx]) + ' '
        idx+=1
        
if questiontype == 2: #Extract Y phrase based on dependency and children
    for word in parse:
        if (word.dep_ == 'nsubj' and word.lemma_ != 'who') or (word.dep_ == 'dobj' or word.dep_ == 'pobj' or word.dep_ == 'nsubjpass'): #Find beginning of subject/object
            children = []
            for child in word.subtree : #Concatenate all childeren of subject
                children.append(child.text)
            Y = str(" ".join(children))
            
# Find Y on wikidata           
params = {'action':'wbsearchentities', 
            'language':'en',
            'format':'json'
            }   
params['search'] = Y
json = requests.get(url,params).json()
obj = json['search'][0]['id']

query ='SELECT ?answer ?answerLabel WHERE { wd:' + obj + ' wdt:' + prop + ' ?answer.' + ' SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}'
url = 'https://query.wikidata.org/sparql'
results = requests.get(url, params={'query': query, 'format': 'json'}).json()
for item in results['results']['bindings']:
    for var in item :
        print('{}\t{}'.format(var,item[var]['value']))
            


# In[ ]:


#questions that worked sorted by rough syntactic structure
# X(noun) Y(noun)
# What is the narrative location of Ford v Ferrari?
# What is the duration of Jason and the Argonauts?
# Who are the voice actors for Adventure Time?

# X(rootverb) Y(noun)
# Who directed Snowpiercer?
# Who casted in Uncut Gems?

# X(rootverb) subX(noun) Y(noun)
# Who designed the costumes for 'les intouchables'?
# Who dubbed the voices for Adventure Time?


# Y(noun) X(rootverb)
# When did Alan Rickman die?
# What was Interstellar influenced by?


# In[ ]:




