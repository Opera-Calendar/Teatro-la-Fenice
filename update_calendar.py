#!/usr/bin/env python3
"""Teatro La Fenice official production pages -> continuously updated opera iCal."""
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm

BASE = 'https://www.teatrolafenice.it'
OUT = Path(__file__).with_name('la-fenice-opera.ics')
TZ = ZoneInfo('Europe/Rome')
MONTHS = {'gennaio':1,'febbraio':2,'marzo':3,'aprile':4,'maggio':5,'giugno':6,
          'luglio':7,'agosto':8,'settembre':9,'ottobre':10,'novembre':11,'dicembre':12}
WEEKDAYS = r'(?:lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)'
DATE_RE = re.compile(rf'\b{WEEKDAYS}\s+(\d{{1,2}})\s+({"|".join(MONTHS)})\s+(20\d{{2}})\s+(\d{{1,2}}):(\d{{2}})\b',re.I)
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; LaFeniceOperaCalendar/1.0; personal calendar subscription)'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url):
    response = SESSION.get(url, timeout=35)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def category_urls():
    """Current/next season; keep discoverable archive category when live."""
    today = datetime.now(TZ).date()
    # La Fenice artistic season normally starts around autumn; check adjacent seasons.
    years = range(today.year - 1, today.year + 3)
    return [f'{BASE}/event-category/opera-{yr}-{str(yr+1)[-2:]}/' for yr in years]


def production_links(soup):
    urls = set()
    for a in soup.select('a[href]'):
        href = urljoin(BASE, a['href'])
        parsed = urlparse(href)
        if parsed.netloc in {'www.teatrolafenice.it','teatrolafenice.it'} and re.match(r'^/event/[^/]+/?$',parsed.path):
            urls.add(href.split('#')[0].split('?')[0])
    return urls


def show_duration(text):
    match = re.search(r'(?:durata(?:\s+dell[’\']opera)?(?:\s+è)?|durata\s+complessiva)\s*[:]?\s*(\d+)\s*or[ea]\s*(?:e\s*)?(\d+)?\s*minut',text,re.I)
    if match:
        return timedelta(hours=int(match[1]),minutes=int(match[2] or 0)),False
    match = re.search(r'(?:durata(?:\s+dell[’\']opera)?(?:\s+è)?|durata\s+complessiva)\s*[:]?\s*(\d+)\s*minut',text,re.I)
    if match:
        return timedelta(minutes=int(match[1])),False
    return timedelta(hours=3),True


def production_events(url):
    soup=fetch(url)
    h1=soup.find('h1')
    if not h1:
        return []
    title=h1.get_text(' ',strip=True)
    text=soup.get_text('\n',strip=True)
    # Venue appears immediately below the production title, before 'vai alla descrizione'.
    # Require an explicit main-stage venue; never default an unknown venue to La Fenice.
    heading=text.split('vai alla descrizione', 1)[0]
    if not re.search(r'(?m)^Teatro La Fenice$', heading):
        logging.info('Skipping non-La Fenice production: %s', url)
        return []
    # The show date links in this official page are ticket links under 'Seleziona una data'.
    date_anchor=[]
    for a in soup.select('a[href]'):
        href=a.get('href','')
        label=a.get_text(' ',strip=True)
        if ('vivaticket.com' in href or 'ACQUISTA' in label.upper()) and DATE_RE.search(label):
            date_anchor.append(label)
    # Keep strictly ticketed date links; do not accidentally parse 'upcoming' sidebar.
    if not date_anchor:
        logging.warning('No dated purchase links: %s',url)
        return []
    location='Teatro La Fenice'
    duration,approx=show_duration(text)
    conductor=re.search(r'(?im)^direttor[ea]\s+([^\n]{3,100})',text)
    description=[f'Produzione: {title}']
    if conductor:description.append('Direzione: '+conductor[1].strip())
    # The full cast often differs by day; link source rather than incorrectly attributing artists.
    if 'LOCANDINA' in text:description.append('Cast e alternanze per data: consultare la locandina ufficiale al link.')
    if approx:description.append('Durata stimata: 3 ore (durata non verificata sul sito).')
    else:description.append('Durata indicata dalla produzione: '+str(duration)+'.')
    description.append('Fonte: '+url)
    entries=[]
    for label in set(date_anchor):
        for match in DATE_RE.finditer(label):
            day,month,year,hour,minute=match.groups()
            start=datetime(int(year), MONTHS[month.lower()],int(day),int(hour),int(minute),tzinfo=TZ)
            if start < datetime.now(TZ) - timedelta(days=1):continue
            entries.append({'title':title,'start':start,'duration':duration,'location':location,
                            'description':'\n'.join(description),'url':url,'approx':approx})
    return entries


def make_calendar(events):
    cal=Calendar()
    cal.add('prodid','-//Opera Calendar//Teatro La Fenice Venezia//DE')
    cal.add('version','2.0')
    cal.add('calscale','GREGORIAN')
    cal.add('method','PUBLISH')
    cal.add('x-wr-calname','Teatro La Fenice – Opera')
    cal.add('x-wr-timezone','Europe/Rome')
    now=datetime.now(timezone.utc)
    for item in sorted(events,key=lambda x:x['start']):
        ev=Event()
        seed=f"{item['url']}|{item['start'].isoformat()}"
        ev.add('uid',hashlib.sha256(seed.encode()).hexdigest()[:24]+'@laf-enice-opera')
        ev.add('dtstamp',now)
        ev.add('summary',item['title']+' – La Fenice')
        ev.add('dtstart',item['start'])
        ev.add('dtend',item['start']+item['duration'])
        ev.add('location',item['location']+', Venezia, Italia')
        ev.add('description',item['description'])
        ev.add('url',item['url'])
        for delta,tag in ((timedelta(days=90),'3 Monate'),(timedelta(days=30),'1 Monat'),
                          (timedelta(days=7),'1 Woche'),(timedelta(days=1),'1 Tag')):
            alarm=Alarm();alarm.add('action','DISPLAY')
            alarm.add('description',item['title']+' – '+tag+' vorher')
            alarm.add('trigger',-delta)
            ev.add_component(alarm)
        cal.add_component(ev)
    return cal


def main():
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    links=set();ok=0
    for category in category_urls():
        try:
            found=production_links(fetch(category))
            if found:ok+=1;links.update(found)
            logging.info('Category %s: %s productions',category,len(found))
        except requests.RequestException as exc:
            logging.warning('Category not available %s: %s',category,exc)
    if not ok or len(links)<3:
        raise RuntimeError('No viable opera season listing; existing calendar preserved')
    events=[];success=0
    for url in sorted(links):
        try:
            found=production_events(url)
            if found:success+=1;events.extend(found)
        except (requests.RequestException,ValueError) as exc:
            logging.warning('Production failed %s: %s',url,exc)
    unique={(e['url'],e['start']):e for e in events}
    if success<2 or len(unique)<5:
        raise RuntimeError(f'Incomplete extraction ({success} works, {len(unique)} shows); existing calendar preserved')
    data=make_calendar(list(unique.values())).to_ical()
    if OUT.exists() and OUT.read_bytes()==data:
        logging.info('No change')
    else:
        OUT.write_bytes(data)
    logging.info('UPDATED: %s productions, %s future performances -> %s',success,len(unique),OUT.name)

if __name__=='__main__':main()
