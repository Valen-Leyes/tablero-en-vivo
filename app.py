import requests
import pytz
from datetime import datetime, timedelta
import streamlit as st
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

import re

def check_horario(horario, time):
    for h in horario:
        if h["time"] <= time < h["next_time"]:
            return h

def get_chaco_data(url):
    response = requests.get(url)
    data = response.json()
    chaco_data = [data['data'].get(f'ubicacion{i}') for i in range(1, 21)]

    # Replace None by empty string
    chaco_data = ["----" if x is None else x for x in chaco_data]

    return chaco_data

def get_rutamil_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_quinielas_data(url, soup, horario):
    quinielas = ["Corrientes", "Nacional", "BuenosAires", "SantaFe", "Cordoba", "EntreRios"]
    tables = []

    # Match horario with table
    horarios = {
        "PREVIA": [0, 0],
        "PRIMERA": [12, 31],
        "MATUTINA": [24, 62],
        "VESPERTINA": [36, 93],
        "NOCTURNA": [48, 124]
    }

    # Get table for horario
    quinielas_data = []

    for quiniela in quinielas:
        result_tag = soup.find('a', {'name': f'Resultados{quiniela}'})
        if result_tag:
            first_table = result_tag.find_next('table', {'style': 'border:#99CC99 4px ridge;border-bottom:0px'})
            second_table = first_table.find_next('table', {'style': 'border:#99CC99 4px ridge;border-top:0px'})
            tables = [first_table, second_table]
            horario_index = horarios[horario["name"]]
            quiniela_data = []
            for i, table in enumerate(tables):
                tds = table.find_all('td')
                numbers = re.findall(r'(\d{4}|----)', tds[horario_index[i]].text.strip())
                if i == 0 and len(numbers) > 5:
                    numbers.pop(0)
                quiniela_data.extend(numbers)
            quinielas_data.append(quiniela_data)
    
    # Append chaco
    chaco_data = get_chaco_data(url)
    quinielas_data.append(chaco_data)
    
    return quinielas_data

def get_cabezas_data(url):
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

def format_cabezas_table(table):
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

def display_cabezas_results(formatted_table):
    columns = st.columns(len(formatted_table[0]))
    for row in formatted_table:
        for column, number in zip(columns, row):
            if number == "Nacional":
                number = "Ciudad B.A."
            elif number == "Buenos Aires":
                number = "Provincia"
            with column:
                # Show in yellow if first
                try:
                    if number == formatted_table[0][formatted_table[0].index(number)]:
                        st.markdown(f'<p style="font-size: 2rem; color: yellow;">{number}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p style="font-size: 2rem;">{number}</p>', unsafe_allow_html=True)
                except ValueError:
                    st.markdown(f'<p style="font-size: 2rem;">{number}</p>', unsafe_allow_html=True)

quinielas = ["corrientes", "ciudad b.a.", "provincia", "santa fe", "cordoba", "entre rios", "chaco"]

argentina = pytz.timezone('America/Argentina/Buenos_Aires')
now = datetime.now(argentina)
if now.weekday() == 6:  # 6 is Sunday
    horarios = [
        {"name": "NOCTURNA", "time": "00:00", "next_time": "23:59"}
    ]
else:
    horarios = [
        {"name": "NOCTURNA", "time": "00:00", "next_time": "10:15"},
        {"name": "PREVIA", "time": "10:15", "next_time": "12:00"},
        {"name": "PRIMERA", "time": "12:00", "next_time": "15:00"},
        {"name": "MATUTINA", "time": "15:00", "next_time": "18:00"},
        {"name": "VESPERTINA", "time": "18:00", "next_time": "21:00"},
        {"name": "NOCTURNA", "time": "21:00", "next_time": "23:59"}
    ]
horario = check_horario(horarios, now.strftime("%H:%M"))
yesterday = now - timedelta(days=1)
if yesterday.weekday() == 6:  # 6 is Sunday
    yesterday -= timedelta(days=1)

date = now.strftime("%Y_%m_%d") if horario["time"] != "00:00" else yesterday.strftime("%Y_%m_%d")

urls = [
    f"https://m.ruta1000.com.ar/index2008.php?FechaAlMinuto={date}&Resultados=Montevideo",
    "https://loteria.chaco.gov.ar/api"
]

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
    quinielas_data = get_cabezas_data(url)
    formatted_table = format_cabezas_table(quinielas_data)
    display_cabezas_results(formatted_table)
else:
    soup = get_rutamil_data(urls[0])
    data = get_quinielas_data(urls[1], soup, horario)
    for quiniela, column in zip(quinielas, columns):
        with column:
            logo_path = logos[quinielas.index(quiniela)]
            quiniela_display = quiniela.upper()
            st.markdown(f'<img src="{logo_path}" style="width: 2rem; vertical-align: middle; margin-right: 0.5rem" /><b style="font-size: 1.25rem">{quiniela_display}</b>', unsafe_allow_html=True)

            for i, row in enumerate(data[quinielas.index(quiniela)], start=1):
                # Show in yellow if first
                if i == 1:
                    st.markdown(f'<p style="font-size: 1.5rem; background-color: black; color: yellow"><span style="font-size: 1.2rem">{f"{i:02d}"}</span>. {row}</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p style="font-size: 0.8rem">{f"{i:02d}"}<span style="font-size: 1.2rem">. {row}</span></p>', unsafe_allow_html=True)

st_autorefresh(interval=1000*15, key="refresh")