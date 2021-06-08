import requests
import time

search_url = 'https://www.wikidata.org/w/api.php'

query_url = 'https://query.wikidata.org/sparql'

search_params = {
    'action': 'wbsearchentities',
    'language': 'en',
    'format': 'json',
}

query_params = {
    'format': 'json',
}

query_template = """
SELECT ?ansLabel
WHERE {{
        wd:{} wdt:{} ?ans.
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}"""

query_how = '''SELECT ?count
                   WHERE {{
                   {{
                       SELECT (COUNT(?item) AS ?count)       # count the amount of properties from the entity
                           WHERE{{
                               wd:{} wdt:{} ?item
                           }}
                   }}
                       SERVICE wikibase:label {{
                       # ... include the labels
                       bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
                       }}
                   }}
          '''


# burocracy
def make_request(what: str, is_prop=False, url=search_url):
    return requests.get(
        url, {
            **({
                'type': 'property'
            } if is_prop else {}), 'search': what,
            **search_params
        }).json()


def make_query(what: str, url=query_url):
    res = requests.get(url, {**query_params, 'query': what})
    if res.status_code != 200:
        raise Exception('Received invalid status code {}: {}'.format(
            res.status_code, res.reason))
    return res.json()


# added a trivial retry policy when there is no results
def run_query(prop, subj, type):
    try:
        subjs = make_request(subj)['search']
        if len(subjs) > 3:
            subjs = subjs[:3]
        props = make_request(prop, True)['search']
        if len(props) > 3:
            props = props[:3]
        for x in range(len(subjs)):
            for y in range(len(props)):
                if type == 1:
                    query = query_how.format(subjs[x - 1]['id'],
                                             props[y - 1]['id'])
                    res = make_query(query)
                    if res['results']['bindings']:
                        return res
                else:
                    query = query_template.format(subjs[x]['id'],
                                                  props[y]['id'])
                    res = make_query(query)
                    if res['results']['bindings']:
                        return res
                time.sleep(1)
    except KeyError:
        return "ERROR"
