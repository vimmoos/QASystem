import spacy


# parsing old type of questions
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


def trivial_question(tokens: list):
    prop, idx = parse_name(tokens[2:], 'of')
    subj, idx = parse_name(tokens[idx + 2:], '?')
    return prop, subj
