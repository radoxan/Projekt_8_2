import streamlit as st
import pandas as pd
from dotenv import dotenv_values
from openai import OpenAI
import fitz  # PyMuPDF
import base64
import instructor
from pydantic import BaseModel
import csv
import os
import numpy as np

st.set_page_config(layout="wide")
csv_name = 'dane.csv'
token = st.sidebar.text_input("Wprowadz token OpenAI")
sidebar_choice = ["Dodawanie elementu", "Przegląd bazy danych"]
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
    if pdf_info.empty:
        st.error("Brak danych do zapisania.")
        return

    dane = [pdf_info.to_dict(orient='records')[0]]
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
                st.text(f"Znaleziono duplikat! Indeks {wiersz['drawing_number']} nie został dodany do bazy!")
            else:
                writer.writerow(wiersz)
                unikalne_dane.add(klucz)
                st.text(f"Indeks {wiersz['drawing_number']} został dodany do bazy!")                

def add_edit_bar(column_name, value_name, type, number_format, key_suffix):
    if type == 'text': 
        if not st.session_state.pdf_info.empty:
            name_value = st.session_state.pdf_info[column_name].iloc[0]
            st.text_input(label=value_name, value=name_value, key=f"{column_name}_{key_suffix}")
        else:
            st.text_input(label=value_name, value='', key=f"{column_name}_{key_suffix}")
    elif type == 'number':
        if not st.session_state.pdf_info.empty:
            name_value = st.session_state.pdf_info[column_name].iloc[0]
            st.number_input(label=value_name, value=float(name_value), format=number_format, key=f"{column_name}_{key_suffix}")
        else:
            st.number_input(label=value_name, value=0.0, format=number_format, key=f"{column_name}_{key_suffix}")
    else:
        print("Wartość type nieprawidłowa")

def update_dataframe_from_inputs(dataframe, row, col):
    key = f"{col}_{row}"
    if key in st.session_state:
        new_value = st.session_state[key]
        if col in ['drawing_number', 'name', 'material', 'additional_note']:
            dataframe.at[row, col] = new_value
        else:
            dataframe.at[row, col] = float(new_value)

st.header("Aplikacja do odczytu danych")

column_names_df = {'drawing_number': [''], 'name': [''], 'height_before_bending': [0], 'width_before_bending': [0], 'model': [0], 
                   'pattern': [0], 'drawing': [0], 'nums_of_corr': [0], 'material': [''], 'thickness': [0], 
                   'bending_radius': [0], 'mass': [0], 'additional_note': [''], 'number_of_bends': [0]}

if 'pdf_info' not in st.session_state:
    st.session_state.pdf_info = pd.DataFrame(column_names_df)
elif isinstance(st.session_state.pdf_info, dict):
    st.session_state.pdf_info = pd.DataFrame([st.session_state.pdf_info])

if choice == sidebar_choice[0]:

    colA1, colA2 = st.columns([5,2])
    with colA1:
        uploaded_file = st.file_uploader("Wybierz plik PDF", type=["pdf"])
    with colA2:
        btn_read_data = st.button("Odczytaj dane")
        btn_save = st.button("Zapisz")
        if btn_save:
            if not st.session_state.pdf_info.empty:
                add_info_to_csv(csv_name, st.session_state.pdf_info)
            else:
                st.error("Brak danych do zapisania. Najpierw odczytaj dane z pliku PDF.")

    colB1, colB2, colB3 = st.columns([5,1,1])
    with colB1:
        if uploaded_file is not None:
            converted_pdf_to_png = convert_pdf_to_png(uploaded_file)
            st.image(converted_pdf_to_png)
            st.data_editor(st.session_state.pdf_info)
            if converted_pdf_to_png:
                image_data = prepare_image_for_open_ai(converted_pdf_to_png)
            else:
                st.error('Nie udało się przekonwertować pliku PDF')
        else:
            st.text("Wczytaj plik .pdf aby wyświetlić rysunek lub wprowadź dane ręcznie")
            st.data_editor(st.session_state.pdf_info)

        if btn_read_data:
            if image_data:
                st.session_state.pdf_info = read_data_from_document(image_data)
                st.data_editor(st.session_state.pdf_info)
            else:
                st.error('Nie udało się przygotować obrazu do OpenAI')
    with colB2:
        add_edit_bar('drawing_number', 'Numer rysunku', 'text', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0, 'drawing_number')    
        add_edit_bar('name', 'Nazwa', 'text', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'name')            
        add_edit_bar('height_before_bending', 'Długość', 'number', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'height_before_bending')
        add_edit_bar('width_before_bending', 'Szerokość', 'number', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'width_before_bending')
        add_edit_bar('thickness', 'Grubość', 'number', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'thickness')
        add_edit_bar('number_of_bends', 'Ilość gięć', 'number', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'number_of_bends')
        add_edit_bar('bending_radius', 'Promień gięcia', 'number', r'%.1f', '0')
        update_dataframe_from_inputs(st.session_state.pdf_info, 0,'bending_radius')

    with colB3:
        add_edit_bar('material', 'Materiał', 'text', r'%.1f', '0')            
        add_edit_bar('mass', 'Waga', 'number', r'%.1f', '0')           
        add_edit_bar('model', 'Model', 'number', r'%.1f', '0')
        add_edit_bar('pattern', 'Wykrój', 'number', r'%.1f', '0')
        add_edit_bar('drawing', 'Rysunek', 'number', r'%.1f', '0')
        add_edit_bar('nums_of_corr', 'Numer poprawki', 'number', r'%.1f', '0')
        add_edit_bar('additional_note', 'Uwagi', 'text', r'%.1f', '0')

if choice == sidebar_choice[1]:
    data_df = pd.read_csv('dane.csv', encoding='ISO-8859-1')
    st.dataframe(data_df)