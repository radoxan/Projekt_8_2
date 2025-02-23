import streamlit as st
import pandas as pd
from dotenv import dotenv_values
from openai import OpenAI
from IPython.display import Markdown, Image
import fitz  # PyMuPDF
import base64
import instructor
from pydantic import BaseModel, create_model
import csv
import os
import json

csv_name = 'dane.csv'
token = st.sidebar.text_input("Wprowadz token OpenAI")
# Lista zakładek
sidebar_choice = ["Dodawanie elementu", "Przegląd bazy danych"]
# Wybór zakładki z listy w sidebar
choice = st.sidebar.radio("Wybierz zakładkę", sidebar_choice)

def prepare_image_for_open_ai(image_data):
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"

def convert_pdf_to_png(uploaded_file, zoom_x=3, zoom_y=3):
    pdf_document = fitz.open(uploaded_file)
    page = pdf_document.load_page(0)
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = page.get_pixmap(matrix=mat)
    img = pix.tobytes("png")
    return img

def read_data_from_document(image_data):
    env = dotenv_values(".env")
    openai_client = OpenAI(api_key=env["OPENAI_API_KEY"])
    instructor_openai_client = instructor.from_openai(openai_client)

    class ImageInfo(BaseModel):
        drawing_number: str
        name: str
        height_before_bending: float
        width_before_bending: float
        model: int
        pattern: int
        drawing: int
        nums_of_corr: int
        material: str
        thickness: float
        bending_radius: float
        mass: float
        additional_note: str
        number_of_bends: int

    info = instructor_openai_client.chat.completions.create(
        model="gpt-4o",
        response_model=ImageInfo,
        messages=[
            {
                "role": "user",
                "content": "Odczytaj z rysunku technicznego elementu giętego z blachy następujące parametry, Nr rysunku, nazwa, wysokość przed gięciem wymiar odczytaj z rozwinięcia z tego samego rzutu co szerokość, szerokość przed gięciem wymiar odczytaj z rozwinięciu z tego samego rzutu co wysokość, model, wykrój, rysunek, ilość pop, Materiał (gatunek bez grubości), grubość blachy, Promień gięcia, Masa, dodatkowa treść po słowie 'Uwaga' jeśli taka występuje. Z rzutu przekroju odczytaj ile element ma gięć."
            },
            {
                "role": "user",
                "content": {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data,
                        "detail": "high"
                    }
                }
            }
        ],
        seed=1
    )

    result = info.model_dump()
    return result

def add_info_to_csv(csv_name, pdf_info):
    dane = [pdf_info]
    plik_istnieje = os.path.isfile(csv_name)
    unikalne_dane = set()

    if plik_istnieje:
        with open(csv_name, mode='r', newline='') as plik:
            reader = csv.DictReader(plik)
            for wiersz in reader:
                unikalne_dane.add((wiersz['drawing_number'], int(wiersz['pattern']), int(wiersz['drawing'])))

    with open(csv_name, mode='a' if plik_istnieje else 'w', newline='') as plik:
        fieldnames = ['drawing_number', 'name', 'height_before_bending', 'width_before_bending', 'model', 
                    'pattern', 'drawing', 'nums_of_corr', 'material', 'thickness', 
                    'bending_radius', 'mass', 'additional_note', 'number_of_bends']
        writer = csv.DictWriter(plik, fieldnames=fieldnames)
        
        if not plik_istnieje:
            writer.writeheader()
        
        for wiersz in dane:
            klucz = (wiersz['drawing_number'], wiersz['pattern'], wiersz['drawing'])
            if klucz in unikalne_dane:
                print(f"Duplikat znaleziony: {wiersz}")
                st.text(f"Znaleziono duplikat! Indeks {wiersz} nie został dodany do bazy!")
            else:
                writer.writerow(wiersz)
                unikalne_dane.add(klucz)
                st.text(f"Indeks {wiersz} został dodany do bazy!")                

st.header("Aplikacja do odczytu danych")

if 'pdf_info_df' not in st.session_state:
    st.session_state.pdf_info_df = []

if 'pdf_info' not in st.session_state:
    st.session_state.pdf_info = None

if choice == sidebar_choice[0]:

    colA1, colA2 = st.columns([5,2])
    with colA1:
        uploaded_file = st.file_uploader("Wybierz plik PDF", type=["pdf"])
    with colA2:
        btn_read_data = st.button("Odczytaj dane")
        btn_save = st.button("Zapisz")
        if btn_save:
            if st.session_state.pdf_info:
                add_info_to_csv(csv_name, st.session_state.pdf_info)
            else:
                st.error("Brak danych do zapisania. Najpierw odczytaj dane z pliku PDF.")

    colB1, colB2 = st.columns([5,2])
    with colB1:
        if uploaded_file is not None:
            converted_pdf_to_png = convert_pdf_to_png(uploaded_file)
            st.image(converted_pdf_to_png)
            if converted_pdf_to_png:
                image_data = prepare_image_for_open_ai(converted_pdf_to_png)
            else:
                st.error('Nie udało się przekonwertować pliku PDF')
        else:
            st.text("Wczytaj plik pdf aby wyświetlić rysunek")

        if btn_read_data:
            if image_data:
                st.session_state.pdf_info = read_data_from_document(image_data)
                st.session_state.pdf_info_df = pd.DataFrame([st.session_state.pdf_info])
                st.data_editor(st.session_state.pdf_info_df)
            else:
                st.error('Nie udało się przygotować obrazu do OpenAI')
    with colB2:
        if not st.session_state.pdf_info_df.empty:
            drawing_number_value = st.session_state.pdf_info_df['drawing_number'].iloc[0]
            st.text_input(label='Numer rysunku', value=drawing_number_value)
        else:
            st.text_input(label='Numer rysunku', value='')

        if not st.session_state.pdf_info_df.empty:
            name_value = st.session_state.pdf_info_df['name'].iloc[0]
            st.text_input(label='Nazwa', value=drawing_number_value)
        else:
            st.text_input(label='Nazwa', value='')

if choice == sidebar_choice[1]:
    data_df = pd.read_csv('dane.csv', encoding='ISO-8859-1')
    st.dataframe(data_df)