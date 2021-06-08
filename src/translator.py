# globals

property_translator = {
    'born': 'birth',
    'die': 'death',
    'directed': 'director',
    'direct': 'director',
    'played': 'performer',
    'performed': 'performer',
    'composed': 'composer',
    'created': 'creator',
    'wrote': 'screenwriter',
    'narrated': 'narrator',
    'owns': 'owned by',
    'produced': 'producer',
    'casted': 'cast',
    'released': 'publication date',
    'première': 'publication date',
}

obj_or_sub = {
    'birth': 0,
    'death': 0,
    'director': 1,
    'performer': 1,
    'composer': 1,
    'creator': 1,
    'screenwriter': 1,
    'narrator': 1,
    'owned by': 1,
    'producer': 1,
    'publication date': 0,
    'cast': 0,
}