#!/usr/bin/env python3
# NOTE: to use this script you should give a number between 0 and 9 as argv
# and it will run the corresponding question.
# If you do not give any arguments to the script
# then it will run all the queries for you
import sys
import requests

questions = [
    {
        'question':
        "How many episode has The Queen's Gambit miniseries?",
        'query':
        """
        SELECT ?episode WHERE{
             wd:Q85808226 wdt:P1113 ?episode.
        }
     """
    },
    {
        'question':
        "How long is in total the Matrix trilogy?",
        'query':
        """
        SELECT (SUM (?duration) as ?total) WHERE{
             wd:Q1210827 wdt:P527 ?films.
             ?films wdt:P2047 ?duration
        }
     """
    },
    {
        'question':
        "What is the main subject of The Matrix trilogy",
        'query':
        """
        SELECT ?subLabel WHERE{
             wd:Q1210827 wdt:P921 ?sub.
             SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
        }
     """
    },
    {
        'question':
        "What are the 5 most recent films about artificial intelligence?",
        'query':
        """
        SELECT DISTINCT ?filmLabel WHERE{
             ?film wdt:P921 wd:Q11660;
                   wdt:P31/wdt:P279* wd:Q11424;
                   wdt:P577 ?date.
             SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
        }
        ORDER BY DESC(?date)
        LIMIT 5
     """
    },
    {
        'question':
        "What are the 5 longest series distributed by Netflix in term of episodes?",
        'query':
        """
        SELECT ?nameLabel WHERE{
             ?name wdt:P750 wd:Q907311;
                   wdt:P1113 ?episode.
             FILTER ( ?episode > 0)
             SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
        }
        ORDER BY DESC (?episode)
        LIMIT 5
     """
    },
    {
        'question':
        "Who is the actor that acted in the Matrix trilogy and has the most number of participation in films?",
        'query':
        """
        SELECT ?nameLabel  WHERE{
            SELECT ?nameLabel (COUNT (DISTINCT ?film) as ?participation) WHERE{
                 wd:Q1210827 wdt:P161 ?name.
                 ?name wdt:P106 wd:Q33999.
                 ?film wdt:P161 ?name.
                 SERVICE wikibase:label { bd:serviceParam wikibase:language
                                         "[AUTO_LANGUAGE],en". }
            } GROUP BY  ?nameLabel
        }
        ORDER BY DESC (?participation)
        LIMIT 1
     """
    },
    {
        'question':
        "What genre of films did Keanu Reeves star in most often?",
        'query':
        """
        SELECT ?genreLabel WHERE{
             SELECT ?genreLabel (COUNT (DISTINCT ?film) as ?cnt) WHERE {
                 ?film wdt:P31 wd:Q11424;
                       wdt:P161 wd:Q43416;
                       wdt:P136 ?genre.
                 SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
             } GROUP BY ?genreLabel
        }
        ORDER BY DESC(?cnt)
        LIMIT 1
     """
    },
    {
        'question':
        "For which film Leonardo DiCaprio won his Academy Awards for Best Actor?",
        'query':
        """
        SELECT ?filmLabel WHERE{
             wd:Q38111 p:P166 ?award.
             ?award ps:P166 wd:Q103916;
                    pq:P1686 ?film
             SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
        }
     """
    },
    {
        'question':
        "Who is the actor/actress that won more Academy Awards for Best Actor/Actress? and how many of them he/she won?",
        'query':
        """
        SELECT ?nameLabel   (COUNT (DISTINCT ?award) as ?cnt) WHERE{
             ?name wdt:P106 wd:Q33999;
                   p:P166 ?award.
             {?award ps:P166 wd:Q103916}
             UNION
             {?award ps:P166 wd:Q103618}
             SERVICE wikibase:label { bd:serviceParam wikibase:language
                                     "[AUTO_LANGUAGE],en". }
        } GROUP BY ?nameLabel
        ORDER BY DESC(?cnt)
        LIMIT 1
     """
    },
    {
        'question':
        "Which are the science fiction films, publicated before 2010, that won more Academy Awards?",
        'query':
        """
        SELECT ?filmLabel WHERE {
             SELECT ?filmLabel (COUNT (DISTINCT ?awards) as ?cnt) WHERE{
                 ?film wdt:P31/wdt:P279*  wd:Q11424;
                       wdt:P136 wd:Q471839;
                       wdt:P166 ?awards;
                       wdt:P577 ?date.
                 ?awards wdt:P31/wdt:P279* wd:Q19020
                 FILTER (year (?date) < 2010)
                 SERVICE wikibase:label { bd:serviceParam wikibase:language
                                          "[AUTO_LANGUAGE],en". }
             } GROUP BY ?filmLabel
        }
        ORDER BY DESC (?cnt)
        LIMIT 10

     """
    },
]

url = 'https://query.wikidata.org/sparql'


def run_query(query: str, who=url):
    return requests.get(who, params={'query': query, 'format': 'json'}).json()


def print_results(data: dict):
    for item in data['results']['bindings']:
        for var in item:
            print(item[var]['value'])


def pretty_query(query: dict):
    print("==========")
    q = query['query']
    print("The following question will be answered:\n", query['question'])
    print()
    res = run_query(q)
    print("The answer is:")
    print()
    print_results(res)
    print("==========")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        if idx >= 10:
            print("The index must be between 0 and 9")
            quit()
        pretty_query(questions[idx])
        quit()
    print("""
 NOTE: to use this script you should give a number between 0 and 9 as argv
 and it will run the corresponding question.
 If you do not give any arguments to the script
 then it will run all the queries for you.
 If you want to run it from a REPL then just call the pretty_query
 function which takes a dictionary with two keys : 'question' and
 'query'. The questions variable contains the list of all these dictionaries.

    """)
    for q in questions:
        pretty_query(q)
