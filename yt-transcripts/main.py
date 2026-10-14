import requests
from docx import Document
from docx.shared import Pt

API_KEY = 'AIzaSyCHH-a7_iGrI0v74V-G3-6_jJx_rQbSWHY'
CHANNELS = [
    "UC5apvpZ8G8T30SdBtkPsacQ",  # Откровения Бехтеревой, 261
    "UCgILLDF-H3fPaqxC2jnT0pA",  # Эпоха Великих Ученых, 202
    "UCpcLggHwr0B4UZKmIx9DCLQ",  # Нейронные открытия Бехтеревой, 63
    "UCyyuU-_pPaaKw82L7Qnl7lQ",  # Наталья Бехтерева рассказывает, 258
    "UCdfeNL54iXtzejfTU1Yku6g",  # Открытия Бехтеревой,
    "UCgqrPxz5bnJjjaHzbAaDg-Q",  # Мудрость
    "UC5apvpZ8G8T30SdBtkPsacQ",  # Бехтеревой объясняется
    "UCTBtAPbC0WwIA_zmkW-Djeg",  # Мысли Бехтеревой
    "UCAwGVn0AX5wJLkbhEo_HPAA",  # Бехтереви и ее мысли
    "UCQ4_p4cttyc5jIf6K08L8wQ",  # Философия жизни | Наталья Бехтерева, 94
    "UCvJ95paukUt-aWpAj8mUF-A",  # Бехтерева и ее мысли, 35
]

def get_all_video_titles(channel_id):
    titles = []
    url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=50&type=video"
    while url:
        resp = requests.get(url).json()
        for item in resp.get('items', []):
            titles.append(item['snippet']['title'])
        url = None
        if 'nextPageToken' in resp:
            url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=50&type=video&pageToken={resp['nextPageToken']}"
    return titles

doc = Document()
for ch_id, ch_name in CHANNELS:
    doc.add_heading(f"{ch_name}, {ch_id}", level=0)
    titles = get_all_video_titles(ch_id)
    for title in titles:
        doc.add_paragraph(title)
    doc.add_page_break()

doc.save("bekhtereva_videos2.docx")
print("Done.")
