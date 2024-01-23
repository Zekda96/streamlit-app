import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import statsmodels.api as sm


# ---------------------------- FUNCTIONS --------------------------------------


def make_p90(dataframe, stat):
    # Make stat p90 where applicable
    if stat in st.session_state['exclude_values_p90']:
        div = 1
    else:
        div = dataframe['90s']

    dataframe.loc[:, stat] = dataframe[stat] / div

    return dataframe


def draw_zones(figure, dfr, xv, yv, hv, vv):
    x_width = 0.05
    y_width = 0.05
    x_margin = (np.max(dfr[xv]) - np.min(dfr[xv])) * x_width
    y_margin = (np.max(dfr[yv]) - np.min(dfr[yv])) * y_width

    x_max = np.max(dfr[xv]) + x_margin
    x_min = np.min(dfr[xv]) - x_margin
    y_max = np.max(dfr[yv]) + y_margin
    y_min = np.min(dfr[yv]) - y_margin

    colors = ["LightSkyBlue", "red", "blue", "yellow"]

    figure.add_shape(type="rect",
                     xref="x",
                     yref="y",
                     x0=x_min,
                     y0=hv,
                     x1=vv,
                     y1=y_max,
                     fillcolor=colors[0],
                     opacity=0.5,

                     )

    figure.add_shape(type="rect",
                     xref="x",
                     yref="y",
                     x0=vv,
                     y0=hv,
                     x1=x_max,
                     y1=y_max,
                     fillcolor=colors[1],
                     opacity=0.1
                     )

    figure.add_shape(type="rect",
                     xref="x",
                     yref="y",
                     x0=x_min,
                     y0=y_min,
                     x1=vv,
                     y1=hv,
                     fillcolor=colors[2],
                     opacity=0.1
                     )

    figure.add_shape(type="rect",
                     xref="x",
                     yref="y",
                     x0=vv,
                     y0=y_min,
                     x1=x_max,
                     y1=hv,
                     fillcolor=colors[3],
                     opacity=0.1
                     )


# ---------------------------- MAPPINGS --------------------------------------
team_colours = {
    'Arsenal': ['#FFFFFF', '#EF0107'],  # 063672
    'Aston Villa': ['#95BFE5', '#670E36'],
    'Bournemouth': ['#DA291C', '#000000'],
    'Brentford': ['#FFFFFF', '#e30613'],
    'Brighton': ['#0057B8', '#FFCD00'],
    'Burnley': ['#6C1D45', '#99D6EA'],
    'Chelsea': ['#034694', '#034694'],
    'Crystal Palace': ['#1B458F', '#A7A5A6'],
    'Everton': ['#003399', '#FFFFFF'],
    'Fulham': ['#000000', '#CC0000'],
    'Leeds United': ['#FFCD00', '#1D428A'],
    'Leicester City': ['#003090', '#FDBE11'],
    'Liverpool': ['#ce1317', '#9a1310'],
    'Manchester Utd': ['#000000', '#DA291C'],
    'Manchester City': ['#6CABDD', '#6CABDD'],
    'Newcastle Utd': ['#241F20', '#FFFFFF'],
    'Norwhich City': ['#FFF200', '#00A650'],
    'Nott\'ham Forest': ['#ff0000', '#ff0000'],
    'Sheffield Utd': ['#EE2737', '#FFFFFF'],
    'Southampton': ['#D71920', '#130C0E'],
    'Tottenham': ['#132257', '#FFFFFF'],
    'Watford': ['#FBEE23', '#ED2127'],
    'West Ham': ['#7A263A', '#1BB1E7'],
    'Wolves': ['#FDB913', '#231F20'],
}

# -------------------------------- DATA ---------------------------------------
df = st.session_state['database']

# ------------------------ Page config ----------------------------------------
st.set_page_config(
    page_title='Análisis de Datos',
    page_icon=':soccer:'
)
# ------------------------------- LAYOUT --------------------------------------
# ------------------------------ Sidebar

# Filter by 90s played
z1, z2 = st.sidebar.select_slider(
    'Filter by 90s',
    options=sorted(df['90s'].unique()),
    value=(np.median(df['90s'].unique()), np.max(df['90s'].unique()))
)

df = df[(df['90s'] >= z1) & (df['90s'] <= z2)]


# positions = st.sidebar.multiselect(
#     label='Positions',
#     # options=['']
# )

# Choose predefined x/y pairs
with st.sidebar.expander('Ejemplos'):
    sc = st.radio(
        label='Elegir scatter predeterminado',
        options=[
            'Eficiencia Goleadora',
            'Eficiencia para Asistir',
            'Acciones Progresivas'
        ],
        index=0,
    )
if sc == 'Eficiencia Goleadora':
    idx = 'npxG'
    idy = 'npG-xG'
elif sc == 'Eficiencia para Asistir':
    idx = 'SCAPassLive'
    idy = 'xAG'
elif sc == 'Acciones Progresivas':
    idx = 'ProgPasses'
    idy = 'ProgCarries'

# Selectbox to choose y value
val_y = st.sidebar.selectbox(
    label='Choose value for y axis',
    options=df.columns.values[12:],
    index=int(np.where(df.columns.values[12:] == idy)[0][0])
)

# Selectbox to choose x value
val_x = st.sidebar.selectbox(
    label='Choose value for x axis',
    options=df.columns.values[12:],
    index=int(np.where(df.columns.values[12:] == idx)[0][0])
)

# Selectbox to highlight team
teams = st.sidebar.multiselect(
    label='Highlight team',
    options=df.team.unique(),
    default=['Manchester City', 'Manchester Utd', 'Chelsea'],
)

# Radio to select trendline or zones to scatterplot
graph_trend = st.sidebar.radio(
    label='Add to plot',
    options=['Trend line', 'Zones'],
    index=1,
)

# Selectbox to choose type of zone lines
if graph_trend == 'Zones':
    zone_lines_type = st.sidebar.selectbox(
        label='Type of Zone Lines',
        options=['Median', 'Average'],
        index=1,
    )

# Format Graph properties
st.sidebar.divider()
st.sidebar.subheader('Format graph')

graph_title = st.sidebar.text_input(label='Title',
                                    value='Scatter plot - Premier League 22/23')

# Player annotations
st.sidebar.divider()
st.sidebar.subheader('Player tags')

players = st.sidebar.multiselect(
    label='Highlight player',
    options=df.player.unique(),
    default=['Erling Haaland', 'Kevin De Bruyne',
             'Marcus Rashford', 'Enzo Fernández'],
)

a_c = st.sidebar.color_picker('Arrow Color', value='#FFFFFF')
st.sidebar.subheader('Edit players\' tag')


# --------------------------------------------------------------------- Content
st.header(':soccer: Scatter Plot Interactivo')
st.subheader('Perfil de Juego y Analisis de Rendimiento')

st.divider()

st.write('Un scatter plot permite una comparacion a base de 2 variables, '
         'las cuales pueden ser complementarias, para analizar '
         'rendimiento, o pueden ser divergentes, para analizar '
         'estilo de juego.\n\n'
         
         'Este grafico es interactivo asi que puede pasar el mouse '
         'encima de los puntos para ver el nombre del jugador.\n\n'
         )

st.divider()

st.write(
         'Para empezar podemos seleccionar una de las 3 opciones en la '
         'pestaña "Ejemplos" ubicada a la izquierda.\n\n')
st.write('**1. Eficiencia Goleadora** muestras 2 variables complementarias: '
         '*Y-Diferencia entre Goles y Goles esperados* y *X-Goles '
         'esperados sin penales*. Mientras mas a la derecha se encuentre '
         'un jugador, mas peligro de gol ha generado con sus tiros, y '
         'mientras '
         'mas arriba este un jugador, mas eficiente es convirtiendo '
         'en gol los tiros que ha hecho. Entonces, fijandonos en la '
         'esquina superior derecha podremos encontrar a los jugadores '
         'con mejor eficiencia goleadora como: **Haaland**, **Rashford** '
         'y **Kane**.\n\n')

st.write('**2. Eficiencia para Asistir** muestra 2 variables complementarias: '
         '*Y-Goles Asistidos Esperados* y *X-Pases que crearon Tiros*. '
         'Mientras mas arriba este un jugador, ha dado pases con mayor '
         'peligro de gol. Mientras que mas a la derecha este un '
         'jugador, ha creado un volumen mas alto de tiros con sus pases. '
         'Fijandonos en la esquina superior derecha podemos destacar a los '
         'jugadores que mayor peligro de gol han creado con sus pases como: '
         '**Kevin De Bruyne** y **Bruno Fernandes**.')

st.write(
         '**3. Acciones Progresivas** muestra 2 variables divergentes: '
         '*Y: Progresion con Drible* y *X: Progresion con Pase*. De '
         'esta manera podemos encontrar jugadores que destaquen '
         'particularmente en *Progresion por drible* en el cuadrante '
         'superior izquierdo, como **Grealish, Saka y Mitoma**. Se pueden '
         'encontrar jugadores que destaquen particularmente en '
         '*Progresion por Pases* en el cuadrante inferior derecho, tales como '
         '**Enzo Fernandez, Alexander-Arnold y Eriksen.** '
         'Y en el cuadrante superior derecho se pueden encontrar los '
         'jugadores singulares que estan por sobre la media en ambas como: '
         '**Kevin De Bruyne**.'
)

st.divider()

# ------------------------------ Scatter 1 ------------------------------------
# val_x = 'npxG'
# val_y = 'CarriesToFinalThird'
df = make_p90(df, val_x)
df = make_p90(df, val_y)

# fig = go.Figure()

# Draw 'other' player markers

df1 = df[~df['team'].isin(teams)]
df1 = df1[~df['player'].isin(players)]

fig = px.scatter(
    df1,
    x=val_x,
    y=val_y,
    # customdata=np.stack([df['player']]),
    # name=customdata[0],
    hover_name='player',
    hover_data='team',
    width=800, height=500,
)

fig.update_layout(
    margin=dict(
        # l=20,
        r=40,
        # t=20,
        # b=20,
    ),
    paper_bgcolor="#050505",
    plot_bgcolor='#131313',
)

# Update 'other players' markers
fig.update_traces(
    marker_size=10,
    marker_color='grey',
    marker_line_width=1,
    opacity=1,
    marker_line_color='#0A0A0A',
)

# Plot markers from highlighted teams
if teams:
    for team in teams:
        df1 = df[df['team'] == team]
        fig = fig.add_scatter(
            x=df1[val_x],
            y=df1[val_y],
            mode='markers',
            name=team,
            hovertext=df1.player.to_list(),
            legendgroup=team,
            # Styling
            marker_size=12,
            marker_color='white',
            marker_line_color='red',
            # marker_symbol='x',
            # marker_opacity=0.5,
            # opacity=0.5,
        )

# Update markers from highlighted teams
if teams:
    for team in teams:
        fig = fig.update_traces(
            selector={'legendgroup': team},
            # marker_color='red',
            marker_line_color=team_colours[team][1],
            marker_color=team_colours[team][0],
            marker_line_width=2.5,
        )

# Highlight players and add sidebar elements to edit each annotation
if players:
    for pl in players:
        with st.sidebar.expander(pl):
            ax = st.text_input(label='ax',
                               value=45,
                               key=f'{pl}_ax')

            ay = st.text_input(label='ay',
                               value=-30,
                               key=f'{pl}_ay')

            t = st.text_input(label='Text',
                              value=pl,
                              key=f'{pl}_text')

            show_a = st.radio(label='Show arrow',
                              options=[True, False],
                              key=f'{pl}_show')
            x_s = st.text_input(label='x shift',
                                value=0,
                                key=f'{pl}_xshift')
            y_s = st.text_input(label='y shift',
                                value=0,
                                key=f'{pl}_yshift')
            marker_c = st.color_picker(label='Marker Color',
                                       value='#FFFFFF',
                                       key=f'{pl}_mc')

        # Create temporary dataset for highlighted player
        dff = df[df['player'] == pl]
        x = dff[val_x].values[0]
        y = dff[val_y].values[0]

        # Add a marker for each player
        fig = fig.add_scatter(
            x=dff[val_x],
            y=dff[val_y],
            mode='markers',
            name=dff.team.values[0],
            hovertext=dff.player.to_list(),
            legendgroup=dff.team.values[0],
            showlegend=False,
            # Styling
            marker_size=12,
            marker_color=marker_c,
            marker_line_color='red',
            # marker_symbol='x',
            # marker_opacity=0.5,
            # opacity=0.5,
        )

        fig.add_annotation(
            x=x,
            y=y,
            ax=ax,
            ay=ay,
            text=t,
            arrowcolor=a_c,
            arrowsize=0.3,
            showarrow=show_a,
            xshift=float(x_s),
            yshift=float(y_s),
        )

# Add Trend line or add zones
if graph_trend == 'Trend line':
    fit_results = sm.OLS(
        df[val_y].values,
        sm.add_constant(df[val_x].values),
        missing="drop"
    ).fit()

    trend_y = fit_results.predict()

    fig = fig.add_trace(
        go.Scatter(
            x=df[val_x],
            y=trend_y,
            showlegend=False,
            mode='lines',
            line_color='blue',
        )
    )

elif graph_trend == 'Zones':

    if zone_lines_type == 'Median':
        hline_val = np.median(df[val_y])
        vline_val = np.median(df[val_x])

    elif zone_lines_type == 'Average':
        hline_val = np.average(df[val_y])
        vline_val = np.average(df[val_x])

    # Add median line for y-axis
    fig.add_hline(
        y=hline_val,
        line_dash="dot",
        line_color="white"
    )

    # Add median line for x-axis
    fig.add_vline(
        x=vline_val,
        line_dash="dot",
        line_color="white"
    )

    # Add zone color backgrounds
    # draw_zones(fig, df, val_x, val_y, hline_val, vline_val)

fig.update_layout(
    title_text=graph_title,
    title_font_size=30,
    title_automargin=True,
)


st.plotly_chart(fig)


st.write('Configuraciones:\n\n'
         '1. Elegir valores de x/y o elegir un ejemplo predeterminado.\n'
         '2. *Opcional: Elegir un equipo para resaltar sus jugadores.*\n'
         '3. Cambiar entre cuadrantes o agregar una linea de tendencia\n'
         '4. Cambiar titulo del grafico\n'
         '5. Elegir jugadores a resaltar\n'
         '6. Editar aspectos visuales de los tags de cada jugador'
         )

st.divider()

st.text('TO-DO\n'
        '- Make stats PAdj\n')
