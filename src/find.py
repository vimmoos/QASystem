import spacy
import src.utils as u


def find_sub_obj(tokens: list):
    sentence = list(tokens.sents)[0]
    sub, obj = None, None
    for child in sentence.root.children:
        if child.dep_ == 'nsubj':
            sub = u.phrase(child)
            continue
        if child.dep_ == 'dobj':
            obj = u.phrase(child)
    return sentence.root, sub, obj


def find_sub_obj_prop_yes_no(tokens: list):
    sentence = list(tokens.sents)[0]
    sub, obj = None, None
    for child in sentence.root.children:
        if child.dep_ == 'nsubj':
            sub = u.phrase(child)
            continue
        if child.dep_ == 'dobj':
            obj = u.phrase(child)
            continue
        if child.dep_ == 'agent' or child.dep_ == 'prep':
            for grandchild in child.children:
                if grandchild.dep_ == 'pobj':
                    obj = u.phrase(grandchild)
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
            if word.text.istitle():
                subject = subject + word.text

    if subject is None:
        for word in tokens:
            if word.dep_ in ['nsubj', 'dobj', 'pobj', 'nsubjpass'
                             ] and word.pos_ not in ['PRON']:
                subject = u.phrase(word)

    # get property of the sentence
    for word in tokens:
        if word.pos_ == 'NOUN':
            property = word.lemma_
            break
        if word.dep_ == 'ROOT' and word.pos_ == 'VERB':
            property = word.lemma_
            break

    return property, subject
