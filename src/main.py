import src.parsing as p
import src.utils as u
import src.burocracy as b
import src.translator as g
import src.auxiliary as aux
import csv
import os
import time


def read_csv(f):
    with open(f, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='|')
        return [row[1] for row in reader]


def run_system(line):
    temp_tok = u.nlp(line)
    if temp_tok[0].text in ["Does", "Did",
                            "Is"]:  #yes/no question requires different output
        prop, sub, obj, type = p.parse_yes_no_question(line.strip())

        print(prop, sub, obj)  #check prop sub and obj
        res_list = b.run_query(prop, sub if temp_tok[0].text == "Is" else obj,
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
        prop, sub, type = p.parse_question(line.strip())
        return b.run_query(prop, sub, type)


def run(line):
    res = None
    try:
        res = run_system(line)
    except Exception as e:
        print("DEBUG: {}".format(e))
    finally:
        if res == None or res == "ERROR":
            time.sleep(1)
            try:
                aux.run_auxiliary(line)
            except Exception as e:
                print("DEBUG: {}".format(e))
                print("No results found")
            return
        else:
            u.print_results(res)


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
