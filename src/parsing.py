import spacy
import src.find as f
import src.translator as g
import src.trivial as t
import src.predicate as p
import src.utils as u


def when_where(tokens: list, root, sub, obj):
    prop, sub = u.basic_sub_obj(root, sub, obj)
    if prop == "publication date": return prop, sub
    return ("date of " + prop, sub) if tokens[0].text == "When" else (
        "place of " + prop, sub) if tokens[0].text == "Where" else (prop, sub)


def parse_yes_no_question(question: str):
    type = 0
    tokens = u.nlp(question.strip())
    prop, sub, obj = f.find_sub_obj_prop_yes_no(tokens)
    print("sub: ", sub, ", obj: ", obj)
    return prop, sub, obj, type


def parse_question(question: str):
    tokens = u.nlp(question.strip())
    type = 0
    if p.is_trivial(tokens):
        prop, sub = t.trivial_question(tokens)
        prop, sub = u.make_string(prop), u.make_string(sub)
    elif p.is_how_many(tokens):
        prop, sub = f.get_prop_sub(tokens[1:] if tokes[-1].text ==
                                   "." else tokens)
        type = 1
    else:
        root, sub, obj = f.find_sub_obj(tokens)
        prop, sub = when_where(tokens, root, sub, obj)
    print("Property: ", prop)
    print("Entity: ", sub)
    return prop, sub, type
