#!/usr/bin/env python 
from re import compile
from sys import argv
from apscheduler.schedulers.background import BackgroundScheduler
from custom_types import get_match, Card
from bs4 import BeautifulSoup
from json import dumps
import requests


def translate(string):
    translations = {
        'goles': 'goals',
        'amarillas': 'yellow_cards',
        'rojas': 'red_cards',
        'cambios': 'subs'
    }
    return translations[string]


def formacion(soup, home_or_away):
    """
    Given a ficha soup, it will return either the formacion table of the home team, or the away one.
    """
    return soup.find('table', attrs={ 'id': f'formacion{home_or_away}' })


def team_name(formacion):
    """
    Given a formacion table, it will find and return the name of the team.
    """
    return formacion.find('td', attrs={ 'class': 'nomequipo' }).string


def incidencia(formacion, incidencia_type):
    """
    Given a formacion table, and an incidencia, that is a string that can be one of: \
    ['amarillas', 'cambios', 'rojas', 'goles'], it will return a string contained in a \
    td of class 'incidencias2'
    """
    # If its a 'gol' the previous tr has a td of class .incidencias1, otherwise it has
    # the same class as the parameter incidencia.
    td_class = 'incidencias1' if incidencia_type is 'goles' else incidencia_type
    prev_sibling_td = formacion.find('td', attrs={ 'class': td_class })
    if prev_sibling_td:
        prev_sibling_tr = prev_sibling_td.parent
        return prev_sibling_tr.next_sibling.find('td', attrs={ 'class': 'incidencias2' })


def parse_minute_and_player(string):
    """
    Given a string like '30\' Some. Player' it deconstructs it into minutes and player
    """
    minute_and_player = dict()
    for subs in string.split('\''):
        try:
            minute_and_player['minute'] = int(subs)
        except ValueError:
            minute_and_player['player'] = subs[1:]
    return minute_and_player



def parse_incidencia(incidencia):
    if incidencia:
        string = incidencia.string
        if '⇆' in string:
            return 'kappa'
        else:
            events = []
            for s in string.split(';'):
                if s is not ' ' or '':
                    events.append(
                        parse_minute_and_player(s[1:] if s.startswith(' ') else s)
                    )
            # return [s for s in string.split(';') if s is not ' ' and s is not '62\' L. Fernandez']
        return events
            
        


def get_changes(url, match_data):
    document = requests.get(url).content
    soup = BeautifulSoup(document, 'lxml')
    
    match_data = dict()
    match_data['match_id'] = url
    for x in range(1, 3):
        a_formacion = formacion(soup, x)
        team = dict()
        team['name'] = team_name(a_formacion)
        for i in ['goles', 'amarillas', 'rojas']:
            incidencias = parse_incidencia(incidencia(a_formacion, i))
            team[translate(i)] = incidencias if incidencias else []
        match_data[
            'home_team' if x is 1 else 'away_team'
        ] = team
    print(dumps(match_data))


def main():
    if len(argv[1:]) != 1:
        print('A match id was not specified, exiting...')
        return 1
    match_id = argv[1:][0]
    
    url = f'http://www.promiedos.com.ar/ficha.php?id={match_id}'

    # Will hold all match data information, when scrapping job is triggered, it'll
    # be compared with another similar dictionary, which has the information
    # currently in the DOM. When the two instances are different an Event will be
    # launched.
    match_data = get_match()

    get_changes(url, match_data)
    return 0


if __name__ == '__main__':
    main()
