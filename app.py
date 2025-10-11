import pandas as pd
import re

import regex
import demoji

import numpy as np
from collections import Counter

import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS

import streamlit as st
import string

###################################
###################################
# Título de la aplicación
st.title('Análisis de nuestro chat de WhatsApp ❤️')
###################################
###################################

##########################################
# ### Paso 1: Definir funciones necesarias
##########################################

# Patron regex para identificar el comienzo de cada línea del txt con la fecha y la hora
def IniciaConFechaYHora(s):
    # Ejemplo: '9/16/23, 5:59 PM - ...'
    # Nuevo patrón para fechas con coma y hora en formato 24h
    # Ejemplo: '27/5/2025, 13:49 - '
    patron = r'^\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2} -'
    return bool(re.match(patron, s))

# Patrón para encontrar a los miembros del grupo dentro del txt
def EncontrarMiembro(s):
    patrones = ['林尚禾🌌:','Estela ✨:']

    patron = '^' + '|'.join(patrones)
    resultado = re.match(patron, s)  # Verificar si cada línea del txt hace match con el patrón de miembro
    if resultado:
        return True
    return False

# Separar las partes de cada línea del txt: Fecha, Hora, Miembro y Mensaje
def ObtenerPartes(linea):
    splitLinea = linea.split(' - ', 1)
    FechaHora = splitLinea[0]                     # '27/5/2025, 13:49'
    splitFechaHora = FechaHora.split(', ')
    Fecha = splitFechaHora[0]                     # '27/5/2025'
    Hora = splitFechaHora[1]                      # '13:49'
    Mensaje = splitLinea[1] if len(splitLinea) > 1 else ''
    if EncontrarMiembro(Mensaje):
        splitMensaje = Mensaje.split(': ', 1)
        if len(splitMensaje) == 2:
            Miembro, Mensaje = splitMensaje
        else:
            Miembro = None
    else:
        Miembro = None
    return Fecha, Hora, Miembro, Mensaje


##################################################################################
# ### Paso 2: Obtener el dataframe usando el archivo txt y las funciones definidas
##################################################################################

# Leer el archivo txt descargado del chat de WhatsApp
RutaChat = 'Data\Chat de WhatsApp con Estela ✨.txt'

# Lista para almacenar los datos (Fecha, Hora, Miembro, Mensaje) de cada línea del txt
DatosLista = []
with open(RutaChat, encoding="utf-8") as fp:
    fp.readline() # Eliminar primera fila relacionada al cifrado de extremo a extremo
    Fecha, Hora, Miembro = None, None, None
    while True:
        linea = fp.readline()
        if not linea:
            break
        linea = linea.strip()
        if IniciaConFechaYHora(linea): # Si cada línea del txt coincide con el patrón fecha y hora
            Fecha, Hora, Miembro, Mensaje = ObtenerPartes(linea) # Obtener datos de cada línea del txt
            DatosLista.append([Fecha, Hora, Miembro, Mensaje])

# Convertir la lista con los datos a dataframe
df = pd.DataFrame(DatosLista, columns=['Fecha', 'Hora', 'Miembro', 'Mensaje'])

# Cambiar la columna Fecha a formato datetime
df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d/%m/%Y")

# Eliminar los posibles campos vacíos del dataframe
# y lo que no son mensajes como cambiar el asunto del grupo o agregar a alguien
df = df.dropna()

# Resetear el índice
df.reset_index(drop=True, inplace=True)

# #### Filtrar el chat por fecha de acuerdo a lo requerido
start_date = '2024-09-01'
end_date = '2025-10-11'

df = df[(df['Fecha'] >= start_date) & (df['Fecha'] <= end_date)]


##################################################################
# ### Paso 3: Estadísticas de mensajes, multimedia, emojis y links
##################################################################

# #### Total de mensajes, multimedia, emojis y links enviados
def ObtenerEmojis(Mensaje):
    emoji_lista = []
    data = regex.findall(r'\X', Mensaje)  # Obtener lista de caracteres de cada mensaje
    for caracter in data:
        if demoji.replace(caracter) != caracter:
            emoji_lista.append(caracter)
    return emoji_lista

# Obtener la cantidad total de mensajes
total_mensajes = df.shape[0]

# Obtener la cantidad de archivos multimedia enviados
multimedia_mensajes = df[df['Mensaje'] == '<Media omitted>'].shape[0]

# Obtener la cantidad de emojis enviados
df['Emojis'] = df['Mensaje'].apply(ObtenerEmojis) # Se agrega columna 'Emojis'
emojis = sum(df['Emojis'].str.len())

# Obtener la cantidad de links enviados
url_patron = r'(https?://\S+)'
df['URLs'] = df.Mensaje.apply(lambda x: len(re.findall(url_patron, x))) # Se agrega columna 'URLs'
links = sum(df['URLs'])

# Obtener la cantidad de encuestas
encuestas = df[df['Mensaje'] == 'POLL:'].shape[0]

# Todos los datos pasarlo a diccionario
estadistica_dict = {'Tipo': ['Mensajes', 'Multimedia', 'Emojis', 'Links', 'Encuestas'],
        'Cantidad': [total_mensajes, multimedia_mensajes, emojis, links, encuestas]
        }

#Convertir diccionario a dataframe
estadistica_df = pd.DataFrame(estadistica_dict, columns = ['Tipo', 'Cantidad'])

# Establecer la columna Tipo como índice
estadistica_df = estadistica_df.set_index('Tipo')

###################################
###################################
st.header('💡 Estadísticas generales')
col1, col2 = st.columns([1, 2])

with col1:
    st.write(estadistica_df)
###################################
###################################

# #### Emojis más usados

# Obtener emojis más usados y las cantidades en el chat del grupo del dataframe
emojis_lista = list([a for b in df.Emojis for a in b])
emoji_diccionario = dict(Counter(emojis_lista))
emoji_diccionario = sorted(emoji_diccionario.items(), key=lambda x: x[1], reverse=True)

# Convertir el diccionario a dataframe
emoji_df = pd.DataFrame(emoji_diccionario, columns=['Emoji', 'Cantidad'])

# Establecer la columna Emoji como índice
emoji_df = emoji_df.set_index('Emoji').head(10)


# Plotear el pie de los emojis más usados
fig = px.pie(emoji_df, values='Cantidad', names=emoji_df.index, hole=.3, template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Pastel2)
fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=20)

# Ajustar el gráfico
fig.update_layout(
    # title={'text': 'Emojis más usados',
    # #          'y':0.96,
    # #          'x':0.5,
    #          'xanchor': 'center'}, font=dict(size=17),
    showlegend=False)
# fig.show()


###################################
###################################
# st.header('Emojis más usados')
# col1, col2 = st.columns([1, 2])

# with col1:
#     st.write(emoji_df)

# with col2:
#     st.plotly_chart(fig)
###################################
###################################

# ### Paso 4: Estadísticas de los miembros del grupo

# #### Miembros más activos

# Determinar los miembros más activos del grupo
df_MiembrosActivos = df.groupby('Miembro')['Mensaje'].count().sort_values(ascending=False).to_frame()
df_MiembrosActivos.reset_index(inplace=True)
df_MiembrosActivos.index = np.arange(1, len(df_MiembrosActivos)+1)
df_MiembrosActivos['% Mensaje'] = (df_MiembrosActivos['Mensaje'] / df_MiembrosActivos['Mensaje'].sum()) * 100

###################################
###################################
with col2:
    st.write(df_MiembrosActivos)
###################################
###################################

# #### Estadísticas por miembro

# Separar mensajes (sin multimedia) y multimedia (stickers, fotos, videos)
multimedia_df = df[df['Mensaje'] == '<Multimedia omitido>']
mensajes_df = df.drop(multimedia_df.index)

# Contar la cantidad de palabras y letras por mensaje
mensajes_df['Letras'] = mensajes_df['Mensaje'].apply(lambda s : len(s))
mensajes_df['Palabras'] = mensajes_df['Mensaje'].apply(lambda s : len(s.split(' ')))
# mensajes_df.tail()


# Obtener a todos los miembros
miembros = mensajes_df.Miembro.unique()

# Crear diccionario donde se almacenará todos los datos
dictionario = {}

for i in range(len(miembros)):
    lista = []
    # Filtrar mensajes de un miembro en específico
    miembro_df= mensajes_df[mensajes_df['Miembro'] == miembros[i]]

    # Agregar a la lista el número total de mensajes enviados
    lista.append(miembro_df.shape[0])
    
    # Agregar a la lista el número de palabras por total de mensajes (palabras por mensaje)
    palabras_por_msj = (np.sum(miembro_df['Palabras']))/miembro_df.shape[0]
    lista.append(palabras_por_msj)

    # Agregar a la lista el número de mensajes multimedia enviados
    multimedia = multimedia_df[multimedia_df['Miembro'] == miembros[i]].shape[0]
    lista.append(multimedia)

    # Agregar a la lista el número total de emojis enviados
    emojis = sum(miembro_df['Emojis'].str.len())
    lista.append(emojis)

    # Agregar a la lista el número total de links enviados
    links = sum(miembro_df['URLs'])
    lista.append(links)

    # Asignar la lista como valor a la llave del diccionario
    dictionario[miembros[i]] = lista
    
# print(dictionario)


# Convertir de diccionario a dataframe
miembro_stats_df = pd.DataFrame.from_dict(dictionario)

# Cambiar el índice por la columna agregada 'Estadísticas'
estadísticas = ['Mensajes', 'Palabras por mensaje', 'Multimedia', 'Emojis', 'Links']
miembro_stats_df['Estadísticas'] = estadísticas
miembro_stats_df.set_index('Estadísticas', inplace=True)

# Transponer el dataframe
miembro_stats_df = miembro_stats_df.T

#Convertir a integer las columnas Mensajes, Multimedia Emojis y Links
miembro_stats_df['Mensajes'] = miembro_stats_df['Mensajes'].apply(int)
miembro_stats_df['Multimedia'] = miembro_stats_df['Multimedia'].apply(int)
miembro_stats_df['Emojis'] = miembro_stats_df['Emojis'].apply(int)
miembro_stats_df['Links'] = miembro_stats_df['Links'].apply(int)
miembro_stats_df = miembro_stats_df.sort_values(by=['Mensajes'], ascending=False)

###################################
###################################
st.subheader('Cómo se distribuyen nuestros mensajes 👀')
st.write(miembro_stats_df)
###################################
###################################



###################################
###################################
st.header('🤗 Emojis más usados')
col1, col2 = st.columns([1, 2])

with col1:
    st.write(emoji_df)

with col2:
    st.plotly_chart(fig)
###################################
###################################



# ### Paso 5: Estadísticas del comportamiento del grupo

df['rangoHora'] = pd.to_datetime(df['Hora'], format='%H:%M')

# Define a function to create the "Range Hour" column
def create_range_hour(hour):
    hour = pd.to_datetime(hour)
    start_hour = hour.hour
    end_hour = (hour + pd.Timedelta(hours=1)).hour
    return f'{start_hour:02d} - {end_hour:02d} h'

# # Apply the function to create the "Range Hour" column
df['rangoHora'] = df['rangoHora'].apply(create_range_hour)
df['DiaSemana'] = df['Fecha'].dt.strftime('%A')
mapeo_dias_espanol = {'Monday': '1 Lunes','Tuesday': '2 Martes','Wednesday': '3 Miércoles','Thursday': '4 Jueves',
                      'Friday': '5 Viernes','Saturday': '6 Sábado','Sunday': '7 Domingo'}
df['DiaSemana'] = df['DiaSemana'].map(mapeo_dias_espanol)
# df


# #### Número de mensajes por rango de hora

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por hora'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
date_df = df.groupby('rangoHora').count().reset_index()

# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='rangoHora', y='# Mensajes por hora', color_discrete_sequence=['salmon'], template='plotly_dark')

# Ajustar el gráfico
# fig.update_layout(
#     title={'text': 'Mensajes con ella ❤️ por hora',
#              'y':0.96,
#              'x':0.5,
#              'xanchor': 'center'},
#     font=dict(size=17))
fig.update_traces(mode='markers+lines', marker=dict(size=10))
fig.update_xaxes(title_text='Rango de hora', tickangle=30)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
###################################
st.header('⏰ Mensajes por hora')
st.plotly_chart(fig)
###################################
###################################


# #### Número de mensajes por día

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por día'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
date_df = df.groupby('DiaSemana').count().reset_index()


# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='DiaSemana', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')

# Ajustar el gráfico
# fig.update_layout(
#     title={'text': 'Mensajes con ella ❤️ por día', 'y':0.96, 'x':0.5, 'xanchor': 'center'},
#     font=dict(size=17))

fig.update_traces(mode='markers+lines', marker=dict(size=10))
fig.update_xaxes(title_text='Día', tickangle=30)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
###################################
st.header('📆 Mensajes por día')
st.plotly_chart(fig)
###################################
###################################

# #### Número de mensajes a través del tiempo

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por día'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
date_df = df.groupby('Fecha').sum().reset_index()

# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='Fecha', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')

# Ajustar el gráfico
# fig.update_layout(
#     title={'text': 'Mensajes con ella ❤️',
#              'y':0.96,
#              'x':0.5,
#              'xanchor': 'center'},
#     font=dict(size=17))

fig.update_xaxes(title_text='Fecha', tickangle=45, nticks=35)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
###################################
st.header('📈 Mensajes a lo largo del tiempo')
st.plotly_chart(fig)
###################################
###################################

# #### Word Cloud de palabras más usadas

import string
# Suponiendo que ya importaste WordCloud, numpy, Image, y nltk.corpus.stopwords

# 1. Definir una lista de palabras románticas (la clave de la modificación)
# Añade todas las palabras que consideres románticas, afectivas o de relación.
palabras_romanticas_objetivo = {
    'amor', 'vida', 'corazón', 'cariño', 'teamo', 'extraño', 'beso', 'besos',
    'abrazo', 'abrazos', 'siempre', 'juntos', 'novio', 'novia', 'querer',
    'feliz', 'alegría', 'hermoso', 'hermosa', 'preciosa', 'cielo', 'princesa',
    'miamor', 'amarte', 'amaría', 'único', 'bonito', 'lindo', 'linda',
    'ojos', 'alma', 'pasión', 'perfecto', 'tequiero', 'sentimiento', 'sentimientos', 'querida'
}

def limpiar_palabras(texto):
    texto = str(texto).lower()
    texto = texto.translate(str.maketrans('', '', string.punctuation))  # elimina puntuación
    return texto.split()
# Reutilizamos el texto_total generado previamente
todas_las_palabras = []
for mensaje in mensajes_df['Mensaje']:
    palabras = limpiar_palabras(mensaje)
    todas_las_palabras.extend(palabras)

# Generar string total
texto_total = ' '.join(todas_las_palabras)

# 2. Filtrar el texto_total para crear un nuevo texto solo con palabras románticas
palabras_limpias = texto_total.split() # Separa el string total en una lista de palabras
palabras_romanticas_filtradas = []

for palabra in palabras_limpias:
    # Asegúrate de que las palabras estén en minúsculas y sin puntuación (como ya hace tu función limpiar_palabras)
    # y verifica si están en el conjunto de palabras románticas objetivo.
    if palabra in palabras_romanticas_objetivo:
        palabras_romanticas_filtradas.append(palabra)

# 3. Generar un nuevo string solo con las palabras románticas
texto_romantico_total = ' '.join(palabras_romanticas_filtradas)

# --- Generación del WordCloud ---

# Carga de máscara (se mantiene igual)
mask = np.array(Image.open('Resources/heart.jpg'))

wordcloud = WordCloud(
    width = 800, height = 800,
    background_color ='black',
    # Ahora las stopwords no son tan críticas, pero puedes usar la lista final_stopwords
    # o una vacía para evitar eliminar accidentalmente palabras románticas si tu lista objetivo no es exhaustiva.
    # Por seguridad, la dejamos como una lista vacía para no interferir con el filtrado por inclusión.
    #stopwords = set(),
    max_words=100, min_font_size = 5,
    mask = mask, colormap='OrRd',
).generate(texto_romantico_total) # Usamos el nuevo texto filtrado

# Plotear la nube de palabras más usadas
# wordcloud.to_image()


###################################
###################################
st.header('❤️ Las palabras que más usamos (Románticas)')
st.image(wordcloud.to_array(), caption='☁️ Nuestro word cloud', use_container_width=True)
###################################
###################################