import src.parsing as p
import src.utils as u
import src.burocracy as b
import src.translator as g

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

# Timo's model
q10 = "Who wrote Titanic?"
q11 = "When was Tom Hanks born? "
q12 = "Who composed the music for Dunkirk?"
q13 = "Who created Star Wars?"
q14 = "Who narrated The Big Lebowski?"
q15 = "Who owns Pixar?"

# Aylar's model
q16 = "How many children does Will Smith have?"
q17 = "How many awards did Morgan Freeman receive?"

# TO DO --> they work in other models
q20 = "When was the première of Iron Man?"  # Timo's model --> doesn't work yet
q21 = "Who are the voice actors for Adventure Time?"  # Lennard's model
q22 = "Who designed the costumes for 'les intouchables'?"  # Lennard's model
q23 = "Who dubbed the voices for Adventure Time?"  # Lennard's model
q24 = "Who casted in Uncut Gems?"  # Lennard's model
q25 = "What was Interstellar influenced by?"  # Lennard's model
q27 = "Which directors were convicted of a sex crime?"  # add query of Aylar's model "4.py"

qs_old = [q0, q1, q2]
qs_sub_obj = [q3, q4, q5, q6, q7, q8, q9]

qs = [*qs_old, *qs_sub_obj, q10, q11, q12, q13, q14, q15]

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
            prop, sub, type = p.parse_question(x)
            print(
                "========\nthe question that is being tested is: {}\nthe answer is"
                .format(x))
            u.print_results(b.run_query(prop, sub, type))
    else:
        temp_tok = u.nlp(line.strip())
        if temp_tok[0].text in ["Does", "Did", "Is"
                                ]:  #yes/no question requires different output
            prop, sub, obj, type = p.parse_yes_no_question(line.strip())
            # try:
            #     prop = property_translator(prop.text)
            # except:
            #     print("hello")
            print(prop, sub, obj)  #check prop sub and obj
            if temp_tok[0].text == "Is":
                res_list = b.run_query(prop, sub, type)
                check = obj
            else:
                res_list = b.run_query(prop, obj, type)
                check = sub
            try:
                yes_no = False
                for item in res_list['results']['bindings']:
                    for var in item:
                        if item[var]['value'] == check:
                            yes_no = True
                if yes_no:
                    print("Yes")
                else:
                    print("No")
                yes_no = False
            except TypeError:
                print("TypeError")
                print("Results: ", res_list)
                print("Check: ", check)

        else:
            prop, sub, type = p.parse_question(line.strip())
            print("the answer is:")
            u.print_results(b.run_query(prop, sub, type))
