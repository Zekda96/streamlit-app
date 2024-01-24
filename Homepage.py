import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------------- Page config
st.set_page_config(
    page_title='Data Analysis',
    page_icon=':soccer:'

)


@st.cache_data()
def read_csv(link):
    return pd.read_csv(link)


# -------------------------------------------------------------- Read Database
if 'database' not in st.session_state:
    st.session_state['database'] = read_csv('data/22-23_fbref_stats.csv')
    # df = read_csv('data/22-23_fbref_stats.csv')
# ----------------------------- DATA ------------------------------------------
# Percentiles
df = st.session_state['database']
pizza = df

# fixtures.loc[:, 'Fecha'] = fixtures_date[0]
pizza = pizza.reset_index(drop=True)

# ------------------------------- LAYOUT --------------------------------------
# ------------------------------- Sidebar
# st.sidebar.write('Hello')
# st.sidebar.button('Press me')

# Content
st.header('Daniel Granja C.')
st.subheader('Análisis y Visualización de Datos :soccer:')

st.write('[[Twitter]](https://twitter.com/DGCFutbol) '
         '[[Instagram]](https://instagram.com/DGCFutbol) '
         '[[Github]](https://github.com/Zekda96) '
         )

st.divider()

s = 'Las siguientes herramientas presentan maneras interactivas de\n' \
    '**visualizar y explorar datos** de jugadores y equipos, las cuales\n' \
    'ejemplifican el uso profesional que se les puede dar para\n' \
    'Scouting, Análisis de Rendimiento, Análisis Táctico, etc.\n\n' \
    'En la barra lateral se encuentran las siguientes ' \
    'herramientas:\n\n' \
    '1. Pizza Charts - Rendimiento de Jugador\n' \
    '2. Scatter Plots - Perfil de Estilo de Juego de Jugadores\n' \
    '3. Chalkboard - Creación de Mapa de Pases'
st.write(s)

st.divider()

# ------------------------------------------------------------------- RANK LIST

st.subheader('Ranking de Rendimiento - Premier League 22/23')

s = "\n\nSe crea un ranking por metrica normalizado\n" \
    "a la cantidad de 90s jugados y filtrado por posición.\n" \
    "En las columnas se puede observar los 90s, el desempeño segun\n" \
    "la metrica, y el ranking de 100 a 0 (100 es el mejor, 0 es el peor)." \
    "\n\n" \
    "1. Elegir metrica (Ej. **npxG** - *Goles esperados sin penales*)\n" \
    "2. Filtrar por posición (Ej. **FW** - *Delanteros*)\n" \
    "3. Filtrar por 90 minutos jugados"

st.write(s)

# with st.expander(label='Glosario'):
#     s = 'npGoals: Goles sin goles de penales\n\n' \
#         'SoT: Tiros al Arco\n\n' \
#         'Sh/90: Tiros c/90 minutos'
#     st.write(s)


# CHOOSE VALUE TO RANK
if 'exclude_values_p90' not in st.session_state:
    st.session_state['exclude_values_p90'] = ['Percent_of_Challenge_Success',
                                              'Sh/90',
                                              'SoT/90'
                                              ]

exclude_values_p90 = st.session_state['exclude_values_p90']

rv_df = df.iloc[:, 12:]  # Exclude categorical columns
ranked_vals = rv_df.select_dtypes(include=np.number).columns.tolist()

s = 'Rank by'
rank_val = st.selectbox(s, ranked_vals, index=13)

# Eliminate columns with 0 on stat to be ranked
pizza = pizza[pizza[rank_val] != 0]

# Make stat p90 where applicable
if rank_val in exclude_values_p90:
    div = 1
else:
    div = df['90s']

pizza.loc[:, rank_val] = df[rank_val] / div

col1, col2, col3 = st.columns(3)
with col1:
    # FILTER BY POSITION
    pos_val = st.multiselect('Choose position',
                             df['pos'].unique(),
                             default=['FW'])
    pizza = pizza[pizza['pos'].isin(pos_val)]

with col2:
    # FILTER BY 90s
    z1, z2 = st.select_slider(
        'Select 90s',
        options=sorted(df['90s'].unique()),
        value=(np.median(df['90s'].unique()), np.max(df['90s'].unique())))
    pizza = pizza[(pizza['90s'] >= z1) & (pizza['90s'] <= z2)]

# Display rank table
cols_to_show = ['player', 'team', '90s', rank_val, 'Rank']

pizza['Rank'] = round(pizza[rank_val].rank(pct=True) * 100, 1)
pizza = pizza.reset_index(drop=True)

st.dataframe(pizza[cols_to_show].sort_values('Rank', ascending=False))

st.divider()

# Hide Streamlit menus
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
