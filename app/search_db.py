import sqlite3

from pymorphy3 import MorphAnalyzer

from config import DB_NAME


morph = MorphAnalyzer()

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cur = conn.cursor()


def search_sequence(request):
    """Для поиска последовательности из нескольких токенов. Возвращает ID предложений и вхождений.
    request = [([entry], search_type)], search_type IN token, lemma, POS, lemma+POS"""
    output = []
    for entry, search_type in request:
        if search_type != 'lemma+POS':
            query = f'SELECT ID_Sent, ID FROM Words WHERE Words.{search_type}=?'
            params = (entry[0],)
        else:
            query = 'SELECT ID_Sent, ID FROM Words WHERE Words.lemma=? AND Words.POS=?'
            params = (entry[0], entry[1])
        res = cur.execute(query, params)
        output.append(res.fetchall())
    return output


def merge_sequence(one, two, first):
    """Для поиска последовательности из нескольких токенов. Возвращает релевантные предложения"""
    res = {}
    second = {}
    
    if first:
        first = {k: [v + 1 for v in vs] for k, vs in first.items()}
    
    for entry in one:
        first.setdefault(entry[0], []).append(entry[1] + 1)
    
    for entry in two:
        if entry[0] in first:
            second.setdefault(entry[0], []).append(entry[1])
    
    for key in second:
        intersection = set(first[key]) & set(second[key])
        if intersection:
            res[key] = list(intersection)
    return res


def search_one(request):
    """Для поиска одного токена. Возвращает релевантные предложения"""
    entry, search_type = request[0]
    if search_type != 'lemma+POS':
        query = f'SELECT DISTINCT Sentence, Author, Name, Link FROM Sentences JOIN Words ON Words.ID_Sent = Sentences.ID WHERE Words.{search_type}=?'
        params = (entry[0],)
    else:
        query = 'SELECT DISTINCT Sentence, Author, Name, Link FROM Sentences JOIN Words ON Words.ID_Sent = Sentences.ID WHERE Words.lemma=? AND Words.POS=?'
        params = (entry[0], entry[1])
    res = cur.execute(query, params)
    return res.fetchall()


def search_db(request):
    """Объединяющая функция поиска.
    request = [([entry], search_type)], search_type IN token, lemma, POS, lemma+POS"""
    if len(request) == 1:
        return search_one(request)
    
    ids = search_sequence(request)
    flag = True
    result = {}
    
    for i in range(len(ids) - 1):
        result = merge_sequence(ids[i], ids[i+1], result if not flag else {})
        flag = False
    
    if result:
        keys = list(result.keys())
        output = []
        for key in keys:
            cur.execute("SELECT Sentence, Author, Name, Link FROM Sentences WHERE ID = ?", (key,))
            output.append(cur.fetchone())
    else:
        output = []
    
    return output


def parse_query(query):
    """Приводит строковой запрос к формату запроса для функции search_db"""
    tokens = query.split()
    parsed_tokens = []
    
    for token in tokens:
        if '"' in token:
            # Поиск точной формы
            parsed_tokens.append(([token.strip('"').lower()], 'token'))
        elif '+' in token:
            # lemma+POS
            lemma, pos = token.split('+')
            parsed_tokens.append(([lemma.lower(), pos], 'lemma+POS'))
        elif token.isupper():
            # Поиск части речи
            parsed_tokens.append(([token], 'POS'))
        else:
            # Поиск леммы
            lemma = morph.normal_forms(token)[0]
            parsed_tokens.append(([lemma], 'lemma'))
    
    return parsed_tokens


def search(query):
    """Главная функция поиска"""
    return search_db(parse_query(query))
