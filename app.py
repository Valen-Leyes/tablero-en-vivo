import requests
import pytz
from datetime import datetime
import streamlit as st
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

def check_horario(horario, time):
    for h in horario:
        if h["time"] <= time < h["next_time"]:
            return h

def get_quiniela_data(url, horario):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table', {'class': 'table table-bordered table-striped'})
    last_table = next((table for table in tables if horario["name"] in str(table)), None)
    if not last_table:
        return []
    trs = last_table.find_all('tr')
    quiniela_data = []
    for tr in trs:
        tds = tr.find_all('td')
        row_data = []
        for td in tds:
            span = td.find('span', {'class': 'nro'})
            if span:
                row_data.append(span.text.strip())
        quiniela_data.append(row_data)
    return quiniela_data

def get_quinielas_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    return table

def replace_accents(text):
    text = text.replace('á', 'a')
    text = text.replace('é', 'e')
    text = text.replace('í', 'i')
    text = text.replace('ó', 'o')
    text = text.replace('ú', 'u')
    text = text.replace('ü', 'u')
    text = text.replace('ñ', 'n')
    return text

def format_quinielas_table(table):
    quinielas = ["Nacional", "Buenos Aires", "Santa Fe", "Cordoba", "Entre Rios", "Corrientes", "Chaco"]

    for span in table.find_all('span', {'class': 'hidden-xs'}):
        span.replace_with('')

    for tag in table.find_all(['a', 'small', 'caption']):
        tag['href'] = '' if tag.name == 'a' else tag.replace_with('')

    for row in table.find('tbody').find_all('tr'):
        quiniela = row.find_all('td')[0].text
        quiniela = replace_accents(quiniela)
        if quiniela not in quinielas:
            row.replace_with('')
    
    # Convert the table into a matrix
    table_matrix = []
    # Add headers
    headers = [cell.text.strip() for cell in table.find('thead').find('tr').find_all('th')]
    table_matrix.append(headers)
    # Add rows
    for row in table.find('tbody').find_all('tr'):
        row_data = [cell.text.strip() for cell in row.find_all('td')]
        table_matrix.append(row_data)

    return table_matrix

quinielas = ["corrientes", "nacional", "buenos aires", "santa fe", "cordoba", "entre rios", "chaco"]
horarios = [
    {"name": "NOCTURNA", "time": "00:00", "next_time": "10:15"},
    {"name": "LA PREVIA", "time": "10:15", "next_time": "12:00"},
    {"name": "LA PRIMERA", "time": "12:00", "next_time": "15:00"},
    {"name": "MATUTINA", "time": "15:00", "next_time": "18:00"},
    {"name": "VESPERTINA", "time": "18:00", "next_time": "21:00"},
    {"name": "NOCTURNA", "time": "21:00", "next_time": "23:59"}
]

argentina = pytz.timezone('America/Argentina/Buenos_Aires')
now = datetime.now(argentina)
horario = check_horario(horarios, now.strftime("%H:%M"))

urls = []

for quiniela in quinielas:
    if quiniela.find(" ") >= 0:
        quiniela = quiniela.replace(" ", "")
    if horario["time"] == "00:00":
        url = f"https://quinieleando.com.ar/quinielas/{quiniela}/resultados-de-ayer"
    else:
        url = f"https://quinieleando.com.ar/quinielas/{quiniela}/resultados-de-hoy"
    urls.append(url)

st.set_page_config(layout="wide")
hide_streamlit_style = """
            <style>
                /* Hide the Streamlit header and menu */
                header {visibility: hidden;}
                /* Optionally, hide the footer */
                .streamlit-footer {display: none;}
                /* Hide your specific div class, replace class name with the one you identified */
                .st-emotion-cache-uf99v8 {display: none;}
                .st-emotion-cache-1ibsh2c {position: absolute; top: -1rem; padding: 0; padding-left: 1rem;}
                .stApp {
                    background-color: #800020;
                }
                p {
                    margin: 0; /* Reduce margin to diminish gap */
                    padding: 0; /* Reduce padding to diminish gap */
                }
            </style>
            """
st.markdown("""
<style>
.stApp {
    background-color: #800020;
}
</style>""", unsafe_allow_html=True)

st.markdown(hide_streamlit_style, unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.3, 0.5])
with col1:
    st.subheader(horario["name"])
with col2:
    today = datetime.now(argentina).strftime("%d/%m/%Y %H:%M")
    st.subheader(today)
with col3:
    st.subheader("AGENCIA OFICIAL 184")
with col4:
    if st.button("Cabezas"):
        if st.session_state.get("cabezas"):
            st.session_state.cabezas = False
        else:
            st.session_state.cabezas = True
columns = st.columns(len(quinielas))

logos = [
    "https://i.ibb.co/hFbspPsM/logo-corrientes.png", 
    "https://play-lh.googleusercontent.com/OtWzhGdgub05KUzdN53Z8CH8zky9LcckUJwZcVMeBLXAMXFxSsEaKEnjmvE1Q75zDCc", 
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWupAplc7Xl-7gaMjMnVd2SolHVZRrQn7g7A&s", 
    "https://i.ibb.co/60d2t8Br/santa-fe-logo.png", 
    "https://pbs.twimg.com/profile_images/946863725352570881/UMyhvPlj_400x400.jpg", 
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ2r78YFe1l_32jxkiZJ3y3t3oM9ALz-Uj2waJCKGAL9Brvdf6aF1-c8JaBX8EhlYxJQUg&usqp=CAU", 
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSazavFAk4DUCYRMywk-Gd3a0AHMVOIH6cJUg&s"
]

if st.session_state.get("cabezas"):
    url = "https://quinieleando.com.ar/quinielas"
    quinielas_data = get_quinielas_data(url)
    formatted_table = format_quinielas_table(quinielas_data)
    columns = st.columns(len(formatted_table[0]))
    for row in formatted_table:
        for column, number in zip(columns, row):
            with column:
                st.markdown(f'<p style="font-size: 3rem;">{number}</p>', unsafe_allow_html=True)
else:
    for quiniela, url, column in zip(quinielas, urls, columns):
        with column:
            logo_path = logos[quinielas.index(quiniela)]
            st.markdown(f'<img src="{logo_path}" style="width: 2rem; vertical-align: middle; margin-right: 0.5rem" /><b style="font-size: 1.25rem">{quiniela.upper()}</b>', unsafe_allow_html=True)
            quiniela_data = get_quiniela_data(url, horario)
            for i, number in enumerate([num for row in quiniela_data for num in row], start=1):
                # Show in yellow if first
                if number == [num for row in quiniela_data for num in row][0]:
                    st.markdown(f'<p style="font-size: 1.5rem; color: yellow"><span style="font-size: 1.2rem">{f"{i:02d}"}</span>. {number}</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p style="font-size: 0.8rem">{f"{i:02d}"}<span style="font-size: 1.2rem">. {number}</span></p>', unsafe_allow_html=True)

st_autorefresh(interval=1000*15, key="refresh")