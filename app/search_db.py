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
    for entry in request:
        if entry[1] != 'lemma+POS':
            query = 'SELECT ID_sent, ID FROM Words WHERE Words.'+ entry[1]+ '="'  + entry[0][0] +'"'
        else:
            query = 'SELECT ID_sent, ID FROM Words WHERE Words.lemma="'  + entry[0][0] + '"AND Words.POS="' + entry[0][1]+'"'
        res = cur.execute(query)
        output.append(res.fetchall())
    return output


def merge_sequence(one, two, first):
    """Для поиска последовательности из нескольких токенов. Возвращает релевантные предложения"""
    res = {}
    second = {}
    if not first:
        for entry in one:
            if entry[0] not in first.keys():
                first[entry[0]] = [entry[1]+1]
            else:
                first[entry[0]].append(entry[1]+1)
    else:
        for key in first:
            first[key] = [value + 1 for value in first[key]]
    for entry in two:
        if entry[0] in first.keys():
            if entry[0] not in second.keys():
                second[entry[0]] = [entry[1]]
            else:
                second[entry[0]].append(entry[1])
    for key in second.keys():
        if set(first[key]) & set(second[key]):
            res[key] = list(set(first[key]) & set(second[key]))
    return res


def search_one(request):
    """Для поиска одного токена. Возвращает релевантные предложения"""
    if request[0][1] != 'lemma+POS':
        query = 'SELECT DISTINCT Sentence, Metadata FROM Sentences JOIN Words ON Words.ID_sent = Sentences.ID WHERE Words.' + request[0][1]+ '="' + request[0][0][0]+'"'
    else:
        query = 'SELECT DISTINCT Sentence, Metadata FROM Sentences JOIN Words ON Words.ID_sent = Sentences.ID WHERE Words.lemma' + '="' + request[0][0][0]+ '" AND Words.POS' + '="' + request[0][0][1] + '"'
    res = cur.execute(query)
    result = res.fetchall()
    return result


def search_db(request):
    """Объединяющая функция поиска.
    request = [([entry], search_type)], search_type IN token, lemma, POS, lemma+POS"""
    if len(request) == 1:
        output = search_one(request)
    else:
        ids = search_sequence(request)
        l = len(ids)
        flag = True
        for i in range(l-1):
            if flag:
                result = merge_sequence(ids[i], ids[i+1], {})
                flag = False
            else:
                result = merge_sequence([],ids[i+1],result)
        if result:
            keys = list(result.keys())
            output = []
            for key in keys:
                cur.execute("SELECT Sentence, Metadata FROM Sentences WHERE ID = ?", (key,))
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
