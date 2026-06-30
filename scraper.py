import requests
from bs4 import BeautifulSoup
import json
import os
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
BASE_URL = 'https://forum.gta5rp.com'

def fetch_servers():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        servers = []
        for node in soup.find_all('h3', class_='node-title'):
            a = node.find('a')
            if a and 'server-no' in a.get('href', ''):
                servers.append({
                    'id': BASE_URL + a.get('href'),
                    'name': a.text.strip(),
                    'url': BASE_URL + a['href']
                })
        return servers
    except Exception as e:
        print("Error fetching servers:", e)
        return []

def find_subforum(url, keywords):
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for a in soup.find_all('h3', class_='node-title'):
        link = a.find('a', href=True)
        if link:
            text_lower = link.text.lower()
            if any(k in text_lower for k in keywords):
                return BASE_URL + link['href']
    return None

def fetch_thread_content(url):
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    messages = soup.find_all('article', class_='message')
    full_content = []
    for message in messages:
        content = message.find('div', class_='bbWrapper')
        if content:
            full_content.append(content.get_text(separator='\n', strip=True))
    
    if full_content:
        return '\n\n'.join(full_content)
    return "Содержимое не найдено."

def parse_server_zb(server_url):
    print(f"Fetching for {server_url}")
    try:
        gos = find_subforum(server_url, ['государственные'])
        if not gos: return []
        gov = find_subforum(gos, ['government', 'правительство'])
        if not gov: return []
        zakon = find_subforum(gov, ['законодательная база'])
        if not zakon: return []
        
        resp = requests.get(zakon, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        data = []
        for div in soup.find_all('div', class_='structItem-title'):
            a_tags = div.find_all('a', href=True)
            if not a_tags: continue
            
            # Filter out prefixes (they have class 'labelLink')
            title_a = next((a for a in a_tags if 'labelLink' not in a.get('class', [])), a_tags[-1])
            
            if title_a and title_a.text.strip():
                title = title_a.text.strip()
                t_lower = title.lower()
                if 'уголовн' in t_lower and ('администрат' in t_lower or 'правонаруш' in t_lower): title = "Уголовно-Административный Кодекс (УАК)"
                elif 'уголовн' in t_lower: title = "Уголовный Кодекс (УК)"
                elif 'администрат' in t_lower or 'правонаруш' in t_lower: title = "Кодекс об Административных Правонарушениях (АК/КОАП)"
                elif 'дорожн' in t_lower: title = "Дорожный Кодекс (ДК)"
                elif 'процессуальн' in t_lower: title = "Процессуальный Кодекс (ПК)"
                elif 'трудов' in t_lower: title = "Трудовой Кодекс (ТК)"
                
                thread_url = BASE_URL + title_a['href']
                content = fetch_thread_content(thread_url)
                
                import re
                parts = re.split(r'(?=\n\s*(?:Статья|Глава|Раздел)\s+)', content)
                articles = []
                for p in parts:
                    if not p.strip(): continue
                    lines = p.strip().split('\n', 1)
                    a_title = lines[0][:100] # Use first line as title
                    a_content = lines[1] if len(lines) > 1 else lines[0]
                    articles.append({"title": a_title, "content": a_content})
                
                if not articles:
                    articles = [{"title": "Текст", "content": content}]
                    
                data.append({
                    "title": title,
                    "articles": articles
                })
                time.sleep(0.5) # rate limit
        return data
    except Exception as e:
        print(f"Error parsing: {e}")
        return []

def get_db_path():
    appdata = os.path.join(os.environ.get('APPDATA', ''), 'ZBHelper')
    if not os.path.exists(appdata):
        os.makedirs(appdata)
    return os.path.join(appdata, 'db.json')

def load_db():
    path = get_db_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_db(data):
    path = get_db_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
