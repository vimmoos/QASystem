import src.translator as g
import spacy

nlp = spacy.load("en_core_web_sm")


def phrase(word):
    children = []
    for child in word.subtree:
        if child.text.istitle():
            children.append(child.text)
    return " ".join(children)


def basic_sub_obj(root, sub, obj):
    try:
        if obj == 'about' or obj == 'shot':
            prop = g.property_translator[obj]
            idx = g.obj_or_sub[prop]
            return prop, sub if idx == 0 else obj
        prop = g.property_translator[root.text]
        idx = g.obj_or_sub[prop]
    except KeyError:
        return None, None
    return prop, sub if idx == 0 else obj


def print_results(data: dict):
    try:
        for item in data['results']['bindings']:
            for var in item:
                print(item[var]['value'])
        print("==========")
    except TypeError:
        print(data)
        print("==========")


def make_string(tokens):
    return " ".join([tok.text for tok in tokens]).rstrip()
