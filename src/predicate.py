# check whether the question is of type "how many"
def is_how_many(tokens):
    if tokens[0].text == "How" and tokens[1].text == "many":
        return True
    return False


def is_trivial(tokens: list):
    fir = tokens[0].text
    # sec = tokens[1].text
    # third = tokens[2].text
    if fir not in ["What", "Who", "When", "Who"]:
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
