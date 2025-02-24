import streamlit as st
import pandas as pd

# Przykładowy DataFrame
column_names_df = {'drawing_number': [''], 'name': [''], 'height_before_bending': [0], 'width_before_bending': [0], 'model': [0], 
                    'pattern': [0], 'drawing': [0], 'nums_of_corr': [0], 'material': [''], 'thickness': [0], 
                    'bending_radius': [0], 'mass': [0], 'additional_note': [''], 'number_of_bends': [0]}
df = pd.DataFrame(column_names_df)

# Inicjalizacja st.session_state.pdf_info_df, jeśli nie istnieje
if 'pdf_info_df' not in st.session_state:
    st.session_state.pdf_info_df = df

# Funkcja do dodawania i edycji wartości w DataFrame
def add_edit_bar(column_name, value_name, type, number_format, key_suffix):
    if type == 'text': 
        if not st.session_state.pdf_info_df.empty:
            name_value = st.session_state.pdf_info_df[column_name].iloc[0]
            st.text_input(label=value_name, value=name_value, key=f"{column_name}_{key_suffix}")
        else:
            st.text_input(label=value_name, value='', key=f"{column_name}_{key_suffix}")
    elif type == 'number':
        if not st.session_state.pdf_info_df.empty:
            name_value = st.session_state.pdf_info_df[column_name].iloc[0]
            try:
                name_value = float(name_value)
            except ValueError:
                name_value = 0.0
            st.number_input(label=value_name, value=name_value, format=number_format, key=f"{column_name}_{key_suffix}")
        else:
            st.number_input(label=value_name, value=0.0, format=number_format, key=f"{column_name}_{key_suffix}")
    else:
        print("Wartość type nieprawidłowa")

def update_dataframe_from_inputs(dataframe, row, col):
    key = f"{col}_{row}"
    if col in ['drawing_number', 'name', 'material', 'additional_note']:
        new_value = st.session_state.get(key, dataframe.at[row, col])
        dataframe.at[row, col] = new_value
    else:
        new_value = st.session_state.get(key, dataframe.at[row, col])
        dataframe.at[row, col] = float(new_value)

# Wyświetlanie i aktualizacja DataFrame
st.write("Oto przykładowy DataFrame:")

add_edit_bar('drawing_number', 'Numer rysunku', 'text', r'%.1f', '0')    
add_edit_bar('name', 'Nazwa', 'text', r'%.1f', '0')         
add_edit_bar('height_before_bending', 'Długość', 'number', r'%.1f', '0')
add_edit_bar('width_before_bending', 'Szerokość', 'number', r'%.1f', '0')
add_edit_bar('thickness', 'Grubość', 'number', r'%.1f', '0')
add_edit_bar('number_of_bends', 'Ilość gięć', 'number', r'%.1f', '0')
add_edit_bar('bending_radius', 'Promień gięcia', 'number', r'%.1f', '0')

update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'drawing_number')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'name')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'height_before_bending')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'width_before_bending')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'thickness')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'number_of_bends')
update_dataframe_from_inputs(st.session_state.pdf_info_df, 0, 'bending_radius')


st.write(st.session_state.pdf_info_df)