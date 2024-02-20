# App
import streamlit as st
from streamlit.connections import BaseConnection
from streamlit_extras.stateful_button import button as st_button
import datetime

# Manage data
import pandas as pd
import numpy as np

# Viz
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch, Standardizer
from matplotlib.patches import FancyArrow
from PIL import Image

# Cloud storage
# from st_supabase_connection import SupabaseConnection
from google.oauth2 import service_account
from google.cloud import bigquery


# """
# mplsoccer uses Statsbomb pitch
# x=120 and y=80
# With a penalty area defined by corners 18p from either end
# (102,18 and 102,62)
# """


# --------------------------------- FUNCTIONS ---------------------------------
# @st.cache_data()
# def read_csv(link):
#     return pd.read_csv(link)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    # df = pd.read_gbq(query, credentials=credentials)
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts
    # Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows


def print_func(name: str):
    now = datetime.datetime.now()
    print(f'[{now}] {name} changed')


def replace_thirds(val):
    if val == 'Start':
        val = 0
    elif val == '1/3':
        val = 1 / 3 * 100
    elif val == '2/3':
        val = 2 / 3 * 100
    elif val == 'End':
        val = 100

    return val


def plot_attacking(ax):
    pitch = Pitch(
        # axis=True,
        # label=True,
        # tick=True,
        goal_type='box',
        line_color=pitch_line_color,
        # line_alpha=0.5,
        linewidth=pitch_line_width,

        # bring the left axis in 10 data units (reduce the size)
        pad_left=pitch_left_pad,
        # bring the right axis in 10 data units (reduce the size)
        pad_right=pitch_right_pad,
        # extend the top axis 10 data units
        pad_top=pitch_top_ad,
        # extend the bottom axis 20 data units
        pad_bottom=0,
    )

    ax.set_facecolor(pitch_bg_color)
    pitch.draw(ax=ax)

    # Figure background color
    fig.patch.set_facecolor(fig_bg_color)

    return pitch


# Standardizer
standard = Standardizer(pitch_from='opta', pitch_to='statsbomb')

# ---------------------------------------------------------------- Page config
st.set_page_config(
    page_title='Análisis de Datos',
    page_icon=':soccer:'
)

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

if "db_loaded" not in st.session_state:
    st.session_state.db_loaded = False
    st.session_state.db = ''

# ------------------------------------------------------------------ LOAD DATA
# df = read_csv('data/2324_events.csv')

# Initialize connection.
# conn = st.connection("supabase", type=SupabaseConnection)

# ------------------------------- DASHBOARD  ----------------------------------
# ---------------------------- SIDEBAR FILTERS --------------------------------
# Filter by league

league = st.sidebar.selectbox(
    label='Select League',
    # options=['Pass'],
    options=['English Premier League',
             'Italian Serie A'
             ],
    # options=df.type.unique(),
    # on_change=league_func()
)

league_names = {'English Premier League': 'EPL',
                'Italian Serie A': 'ITA'}
league_short = league_names[league]

# Filter by season
season = st.sidebar.selectbox(
    label='Select Season',
    # options=['Pass'],
    options=['23/24'],
    # options=df.type.unique(),
)

season_short = season.replace('/', '')

db = st.secrets["gbq_table"]['events_db']
table = f"{db}.{league_short}{season_short}"

# Filter by type of event
event = st.sidebar.selectbox(
    label='Select event',
    options=['Pass'],
    # options=['Pass', 'Goal'],
    # options=df.type.unique(),
)

all_teams = run_query(
    f'''
        SELECT DISTINCT team from `{table}`
        ORDER BY team ASC
        '''
)

all_teams = [row['team'] for row in all_teams]

# if 'team' not in st.session_state:
#     st.session_state.team = ''

# Selectbox to highlight team
st.sidebar.selectbox(
    label='Select team',
    options=all_teams,
    index=7,
    key='team',
    on_change=print_func('team_selectbox')
)

team = st.session_state.team

matches_played = len(run_query(
    f'''
    SELECT DISTINCT home, away FROM `whoscored_events.{league_short}{season_short}`
    WHERE team = '{team}'
    '''
)
)

# Return only selected type of events from selected team
# Run query when button is pressed
if st.sidebar.button(label='Cargar Base de Datos', key='button1'):
    st.session_state.db_loaded = True
    st.session_state.db = pd.DataFrame(
        run_query(
            f'''
            SELECT home, away, team, player,
            outcome_type, type, x, y, end_x, end_y, length
            FROM `{table}`
            WHERE type = '{event}'
                AND team = '{team}'
'''
        )
    )

# ------------------------------- MAIN PAGE  ----------------------------------

# # Load fonts
# font_normal = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/roboto/Roboto%5Bwdth,wght%5D.ttf')
# font_italic = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/roboto/Roboto-Italic%5Bwdth,wght%5D.ttf')
# font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf')

st.title('Chalkboard :soccer:')
st.subheader('Creacion de mapas de pases')
st.write(f'{league} {season} - {matches_played} Partidos')

# -------------------------------------------------------------- Read Database

if st.session_state.db_loaded:
    print('Load session-state-db to df')
    df = st.session_state.db
    # Events
    team_colors = {'Chelsea': '#0b4393',
                   'Manchester United': '#de0011',
                   'Liverpool': '#f30022',
                   'Arsenal': '#db0007',
                   'Tottenham': '#0f1f4a',
                   'Aston Villa': '#650334',
                   'Newcastle United': '#231f20',
                   'Manchester City': '#1683E2',
                   }

    if team in team_colors.keys():
        event1_marker_color1 = team_colors[team]
    else:
        event1_marker_color1 = team_colors['Chelsea']

    # Return players from team

    # Selectbox to choose players of interest
    players = st.sidebar.multiselect(
        label='Select players',
        options=df[df['team'] == team].player.dropna().sort_values().unique(),
        default=df[df['team'] == team].player.dropna().sort_values().unique()[
            11],
    )

    # Filter by actions against opposing team
    # Local teams when away is the team of interest PLUS
    # away teams when local is team of interest
    rivals_opt = df.loc[df['home'] == team, 'away'].unique().tolist()
    rivals_opt += df.loc[df['away'] == team, 'home'].unique().tolist()
    rivals_opt.sort()
    rivals = st.sidebar.selectbox(
        label='Select rivals',
        options=rivals_opt,
        # default=rivals_opt[0],
    )

    rivals = [rivals]

    if event == 'Pass':
        # Granular filter by pitch length
        l1, l2 = st.sidebar.select_slider(
            # label='Select Pass Length (m)',
            label='Seleccionar Distancia de Pase (metros)',
            # Not eliminating the NAN messed up the sorting
            options=sorted(df[df['length'].notna()].loc[:, 'length'].unique()),
            # options=sorted(df['length'].unique()),
            value=(np.min(df['length'].dropna().unique()),
                   np.max(df['length'].dropna().unique())
                   )
        )
        # Filtering occurs here
        df = df[(df['length'] >= l1) & (df['length'] <= l2)]

    # Filter by Starting Pitch Zone
    x1, x2 = st.sidebar.select_slider(
        # 'Filter by Starting Pitch Zone',
        'Zona de Inicio del pase',
        options=('Start', '1/3', '2/3', 'End'),
        value=('Start', 'End'),
    )
    x1 = replace_thirds(x1)
    x2 = replace_thirds(x2)

    # Filter by Receiving Pitch Zone
    end_x1, end_x2 = st.sidebar.select_slider(
        # 'Filter by Receiving Pitch Zone',
        'Zona de Recepcion del Pase',
        options=('Start', '1/3', '2/3', 'End'),
        value=('Start', 'End'),
    )
    end_x1 = replace_thirds(end_x1)
    end_x2 = replace_thirds(end_x2)

    if len(players) > 0:
        title_text = st.sidebar.text_input(
            # label='Figure Title',
            label='Titulo de Figura 1',
            value=f'{players[0]} Passes'
        )

    title_text2 = st.sidebar.text_input(
        # label='2nd Figure Title',
        label='Titulo de Figura 2',
        value=f'{team} Passes'
    )
    # ------------------------------ FILTER DATA ----------------------------------
    # Filter by team
    plot_df = df[df['team'] == team]

    # Filter only actions against selected teams
    plot_df = plot_df[
        ((plot_df['home'] == team) & (plot_df['away'].isin(rivals)))
        |
        ((plot_df['home'].isin(rivals)) & (plot_df['away'] == team))
        ]

    # Length filtering occurs at after the length slider code as that slider
    # is conditional and might not appear all the time.
    # Filtering pseudo-code for reference;
    # and (df['length'] >= l1) and (df['length'] <= l2)

    # Filter by Starting Pitch Zone

    plot_df = plot_df[
        (plot_df['x'] >= x1)
        & (plot_df['x'] <= x2)
        ]

    # Filter by Receiving Pitch Zone
    plot_df = plot_df[
        (plot_df['end_x'] >= end_x1)
        & (plot_df['end_x'] <= end_x2)
        ]

    # Dataframe used for showing table and for multi-player plot
    team_df = plot_df[['player', 'type', 'outcome_type',
                       'x', 'y', 'end_x', 'end_y']]
    # FILTERING BY PLAYER IS DONE LAST SO WE CAN GET THE FILTERED DF OF ALL PLAYERS
    # Filter by player
    plot_df = plot_df[plot_df['player'].isin(players)]

    # ------------------------- COUNT DATA
    # --- Dataframe with team events

    # Count and get % of total
    team_events = team_df.count()['player']
    # Successful - Count
    scc_team = team_df[team_df['outcome_type'] == 'Successful'].count()[
        'player']
    # Unsuccessful
    fail_team = team_df[team_df['outcome_type'] == 'Unsuccessful'].count()[
        'player']

    # --- Dataframe with only player events
    player_df = {}
    player_events = {}
    p = {}
    scc_player = {}
    player_cmp = {}
    fail_player = {}
    for player in players:
        player_df[player] = team_df[team_df['player'] == player]
        # Count and get % of total
        player_events[player] = player_df[player].count()['player']

        if team_events > 1:
            p[player] = round(player_events[player] / team_events * 100, 1)
        else:
            p[player] = 0.0

        # Successful - Count
        scc_player[player] = \
            player_df[player][team_df['outcome_type'] == 'Successful'].count()[
                'player']

        if player_events[player] > 0:
            player_cmp[player] = round(
                scc_player[player] / player_events[player] * 100, 1)
        else:
            player_cmp[player] = 0.00

        # Unsuccessful

        fail_player[player] = \
            player_df[player][
                team_df['outcome_type'] == 'Unsuccessful'].count()[
                'player']

    # ------------------ SORT TOP 5 PLAYERS
    top = team_df[['player', 'type']].groupby(['player']).agg('count')
    top = top.sort_values(by=['type'], ascending=False).head()

    # ------------------------------ FORMAT PLOT ----------------------------------
    # -------------------------- EDIT/CHANGE PARAMETERS

    image_path = 'images/ch.png'
    # Figure
    margin1 = 5
    # Pitch Padding
    pitch_left_pad = 0
    pitch_right_pad = 0
    pitch_top_ad = 0
    pitch_bottom_pad = 0
    # pitch_bottom_pad = -35

    # Figure Background Color
    fig_bg_color = '#faf9f4'

    # Grid
    # Grid Settings
    # fig_w_pixels = 1000
    # fig_h_pixels = 1000
    # fig_width = fig_w_pixels/80
    # fig_height = fig_h_pixels/80
    nrows = 1
    ncols = 1
    max_grid = 1
    grid_space = 0

    # Figure ratios between sections (title, pitch, credits)

    title_h = 0.1  # the title takes up 15% of the fig height
    grid_h = 0.7  # the grid takes up 71.5% of the figure height
    endnote_h = 0.1  # endnote takes up 6.5% of the figure height

    grid_w = 0.5  # grid takes up 95% of the figure width
    left_p = 0.1

    title_space = 0.01  # 1% of fig height is space between pitch and title
    endnote_space = 0.00  # 1% of fig height is space between pitch and endnote

    space = 0.01  # 5% of grid_height is reserved for space between axes

    # --- Figure: Title
    # - Title
    title_x = 0.5
    title_y = 0.9
    title_ha = 'center'
    title_va = 'top'
    title_size = 17

    # - Subtitle1
    subtitle1_x = 0.5
    subtitle1_y = 0.38
    subtitle1_ha = 'center'
    subtitle1_va = 'center'
    subtitle1_size = 12

    subtitle1_text = f"{season} Season | {league[8:]} | vs. {rivals[0]}"

    subtitle1_color = "#030303"

    # - Subtitle2
    subtitle2_x = 0.5
    subtitle2_y = 0.2
    subtitle2_ha = 'center'
    subtitle2_va = 'center'
    subtitle2_size = 10

    subtitle2_text = f"{season} | League only | Last 5 Matches | As of Nov 25, 2023"
    subtitle2_color = "#030303"

    # --- Figure: Pitch
    pitch_line_width = 0.8
    pitch_line_color = '#03191E'
    pitch_bg_color = '#faf9f4'

    event2_marker_color1 = '#B5B4B2'
    event_line_width1 = 1.8

    event_marker_width1 = 12

    is_line_transparent = True
    line_alpha_start = 0.1
    line_alpha_end = 1

    # Legend
    legend_ref = 'lower center'
    legend_loc = (0.5, -0.22)  # Loc. of the lower center of the Legend
    if len(players) > 0:  # To avoid error messages when no player is selected yet
        # label1 = f'{scc_player[players[0]]} Completed passes'
        label1 = f'{scc_player[players[0]]} Completados'
        # label2 = f'{player_events[players[0]] - scc_player[players[0]]} Missed passes'
        label2 = f'{player_events[players[0]] - scc_player[players[0]]} Fallados'

    legend_bg_color = 'white'
    legend_edge_color = 'black'
    legend_text_color = 'black'
    legend_alpha = 1

    # --- Figure: Credits

    # --------------------------- PLOT 2 PARAMETERS -------------------------------
    # Figure
    margin = 7
    # Title
    title_size2 = 30

    title_x2 = 0.089
    title_y2 = 0.9
    title_ha2 = 'left'
    title_va2 = 'top'

    # Subtitle
    subtitle1_text2 = f'{season} {league[8:]} | vs. {rivals[0]} | ' \
                      f'Top 3 Players with Most Attempted Passes'
    subtitle_size2 = 16

    subtitle1_x2 = 0.091
    subtitle1_y2 = 0.5725

    subtitle1_ha2 = 'left'
    subtitle1_va2 = 'top'

    # Font size
    player_names_size = 18  # Players name title over each pitch
    data1_size = 14  # Total passes text

    # Legend
    legend_ref2 = 'lower center'
    # legend_loc2 = (0.5, -0.008)  # Loc. of the lower center of the Legend
    legend_loc2 = (0.5, 0.1425)  # Loc. of the lower center of the Legend

    legend_bg_color2 = 'white'
    legend_edge_color2 = 'black'
    legend_text_color2 = 'black'
    legend_alpha2 = 1


    def label_completed2(dfp, p, i):
        return f'{dfp[p[i]]} completed'


    def label_missed2(df1, df2, pl, ix):
        t = f'{df1[pl[ix]] - df2[pl[ix]]}' \
            f' missed'
        return t


    # label_completed2 = f'{scc_player[players[i]]} completed'
    # label_missed2 = f'{player_events[players[i]] - scc_player[players[i]]} missed'

    # Events
    event1_marker_color2 = event1_marker_color1
    event2_marker_color2 = event2_marker_color1
    # '#ef4146'  # chelsea red for markers facecolor
    event_line_width2 = 3

    event_marker_width2 = 12

    is_line_transparent = True
    line_alpha_start2 = 0.1
    line_alpha_end2 = 0.3

    # ----------------------------- SETUP FIGURE

    # Tabs for stats select
    # tab_one, tab_two, tab_four = st.tabs([
    #     "One Un Jugador",
    #     "Tres Jugadores",
    #     "En Desarrollo...",
    # ]
    # )

    tab_one, tab_two = st.tabs([
        "Un Jugador",
        "Tres Jugadores"
    ]
    )
    with tab_one:
        if len(players) != 1:
            # st.caption('This viz requires only 1 player selected.')
            st.caption('Selecciona solo 1 jugador.')

        else:
            pitch = Pitch(
                # axis=True,
                # label=True,
                # tick=True,
                goal_type='box',
                line_color=pitch_line_color,
                # line_alpha=0.5,
                linewidth=pitch_line_width,

                # bring the left axis in 10 data units (reduce the size)
                pad_left=pitch_left_pad,
                # bring the right axis in 10 data units (reduce the size)
                pad_right=pitch_right_pad,
                # extend the top axis 10 data units
                pad_top=pitch_top_ad,
                # extend the bottom axis 20 data units
                pad_bottom=pitch_bottom_pad,
            )

            fig, axs = pitch.grid(
                nrows=1, ncols=1,
                figheight=7,

                title_height=title_h,
                # the title takes up 15% of the fig height
                grid_height=grid_h,
                # the grid takes up 71.5% of the figure height
                endnote_height=endnote_h,
                # endnote takes up 6.5% of the figure height
                #
                grid_width=grid_w,  # gris takes up 95% of the figure width
                #
                # # 1% of fig height is space between pitch and title
                title_space=title_space,
                #
                # # 1% of fig height is space between pitch and endnote
                endnote_space=endnote_space,
                #
                space=space,
                # 5% of grid_height is reserved for space between axes
                #
                # # centers the grid horizontally / vertically
                left=left_p,
                bottom=None,
                axis=False,
            )

            # ------------ Add 3rds Lines
            x, _ = standard.transform([1 / 3 * 100, 2 / 3 * 100], [0, 0])

            axs['pitch'].vlines(
                x=x,
                ymin=-1,
                ymax=81,
                colors='black',
                linestyles='dashed',
                alpha=0.5,
                clip_on=False,
            )

            # Add 'Direction of Play' Arrow
            l1 = FancyArrow(x=0.2, y=0.1, dx=0.3, dy=0,
                            transform=fig.transFigure, figure=fig,
                            length_includes_head=True,
                            head_length=0.01,
                            head_width=0.0225,
                            color='black')

            fig.lines.extend([l1])

            axs['pitch'].text(x=60, y=84,
                              s='Dirección de Ataque',
                              ha='center',
                              size='10.5',
                              )

            # Figure background color
            fig.patch.set_facecolor(fig_bg_color)
            # Pitch background color
            axs['pitch'].set_facecolor(pitch_bg_color)

            # Add invisible text to add margins
            axs['pitch'].text(
                x=-margin1,
                y=60,
                s='o',
                c=fig_bg_color,
                # c='red',
                ha='center',
            )
            axs['pitch'].text(
                x=120 + margin1,
                y=60,
                s='o',
                c=fig_bg_color,
                # c='red',
                ha='center',
            )

            # Add title
            axs['title'].text(
                x=title_x,
                y=title_y,
                s=title_text,
                size=title_size,
                ha=title_ha,
                va=title_va,
            )

            # Add subtitle 1
            axs['title'].text(
                x=subtitle1_x,
                y=subtitle1_y,
                s=subtitle1_text,
                size=subtitle1_size,
                ha=subtitle1_ha,
                va=subtitle1_va,
                # fontproperties=font_bold.prop,
                color=subtitle1_color,
            )

            # # Add subtitle 2
            # axs['title'].text(
            #     x=subtitle2_x,
            #     y=subtitle2_y,
            #     s=subtitle2_text,
            #     size=subtitle2_size,
            #     ha=subtitle2_ha,
            #     va=subtitle2_va,
            #     # fontproperties=font_bold.prop,
            #     color=subtitle2_color,
            # )

            # axs['pitch'].set_ylabel('Undamped')
            # axs['pitch'].set_axis = True

            # Draw passes
            if event == 'Pass':
                # Unsuccessful Passes
                pdf = plot_df[plot_df['outcome_type'] == 'Unsuccessful']
                xstart, ystart = standard.transform(pdf['x'], pdf['y'])
                xend, yend = standard.transform(pdf['end_x'], pdf['end_y'])

                pitch.lines(
                    xstart=xstart,
                    ystart=ystart,
                    xend=xend,
                    yend=yend,
                    comet=is_line_transparent,
                    # color='#c1c1bf', # BenGriffis gray
                    color=event2_marker_color1,
                    ax=axs['pitch'],
                    lw=event_line_width1,
                    label=label2,
                    transparent=is_line_transparent,
                    alpha_start=line_alpha_start,
                    alpha_end=line_alpha_end,
                )

                pitch.scatter(
                    x=xend,
                    y=yend,
                    ax=axs['pitch'],
                    s=event_marker_width1,
                    linewidth=0,
                    marker='o',
                    facecolor=event2_marker_color1,
                )

                # Successful Passes
                pdf = plot_df[plot_df['outcome_type'] == 'Successful']
                xstart, ystart = standard.transform(pdf['x'], pdf['y'])
                xend, yend = standard.transform(pdf['end_x'], pdf['end_y'])

                pitch.lines(
                    xstart=xstart,
                    ystart=ystart,
                    xend=xend,
                    yend=yend,
                    comet=True,
                    color=event1_marker_color1,
                    ax=axs['pitch'],
                    lw=event_line_width1,
                    label=label1,
                    transparent=is_line_transparent,
                    alpha_start=line_alpha_start,
                    alpha_end=line_alpha_end,
                )

                pitch.scatter(
                    x=xend,
                    y=yend,
                    ax=axs['pitch'],
                    s=event_marker_width1,
                    marker='o',
                    facecolor=event1_marker_color1,
                )

            # # Add 'Middle 3rd' and 'Final 3rd' Labels
            # props = dict(
            #     boxstyle='round, pad=0.9',
            #     facecolor=fig_bg_color,
            #     alpha=0.5
            # )

            # axs['pitch'].add_patch(Rectangle((1, 1), 2, 6,
            #              edgecolor = 'pink',
            #              facecolor = 'blue',
            #              fill=True,
            #              lw=5)
            #                        )

            # axs['pitch'].text(
            #     x=83,
            #     y=68,
            #     s='Middle 3rd',
            #     rotation=270,
            #     size=15,
            #     verticalalignment='top',
            #     # bbox=props,
            # )

            # ------------ Add Legend
            legend = axs['pitch'].legend(
                facecolor=legend_bg_color,
                # handlelength=5,
                edgecolor=legend_edge_color,
                # prop=robotto_regular.prop,
                labelcolor=legend_text_color,
                framealpha=legend_alpha,
                loc=legend_ref,
                bbox_to_anchor=legend_loc,
            )

            # ------------ Add Credits
            fig.text(
                0.597,
                0.17,
                '@DGCFutbol',
                va='top',
                ha='right',
                fontsize=11,
                weight='bold',
                # ontproperties=robotto_regular.prop,
                color=event1_marker_color1,
                alpha=0.3,
            )

            axs['endnote'].text(
                1,
                0.1,
                'Gráficos: Daniel Granja C.\n@DGCFutbol',
                va='top',
                ha='right',
                fontsize=9,
                weight='bold',
                # ontproperties=robotto_regular.prop,
                color=event1_marker_color1,
                alpha=0.4,
            )

            # DRAW FIG
            st.pyplot(fig)

    # -------------------------- SETUP MULTIGRID FIGURE
    with tab_two:
        if len(players) != 3:
            # st.caption('This viz requires only 3 players selected.')
            st.caption('Selecciona solo 3 jugadores.')

        else:
            pitch2 = VerticalPitch(
                # axis=True,
                # label=True,
                # tick=True,
                goal_type='box',
                line_color=pitch_line_color,
                # line_alpha=0.5,
                linewidth=pitch_line_width * 2,

                # bring the left axis in 10 data units (reduce the size)
                pad_left=pitch_left_pad,
                # bring the right axis in 10 data units (reduce the size)
                pad_right=pitch_right_pad,
                # extend the top axis 10 data units
                pad_top=pitch_top_ad,
                # extend the bottom axis 20 data units
                pad_bottom=0,
            )

            fig2, axs2 = pitch2.grid(
                nrows=1, ncols=len(players),
                figheight=10,

                title_height=0.15,  # the title takes up 15% of the fig height
                grid_height=0.7,
                # the grid takes up 71.5% of the figure height
                endnote_height=0.03,
                # endnote takes up 6.5% of the figure height

                grid_width=0.5,  # gris takes up 95% of the figure width

                # 1% of fig height is space between pitch and title
                title_space=0.035,

                # 1% of fig height is space between pitch and endnote
                endnote_space=0.01,

                space=0.1,
                # 5% of grid_height is reserved for space between axes

                # centers the grid horizontally / vertically
                left=0,
                bottom=None,
                axis=False,
            )

            # Figure background color
            fig2.patch.set_facecolor(fig_bg_color)

            # Add invisible text to add margins
            axs2['pitch'][0].text(
                x=-margin,
                y=50,
                s='o',
                c=fig_bg_color,
            )
            axs2['pitch'][len(players) - 1].text(
                x=80 + margin,
                y=50,
                s='o',
                c=fig_bg_color,
            )
            # Add title
            axs2['title'].text(
                x=title_x2,
                y=title_y2,
                s=title_text2,
                size=title_size2,
                ha=title_ha2,
                va=title_va2,
                # weight='bold',
            )

            # Add subtitle 1
            axs2['title'].text(
                x=subtitle1_x2,
                y=subtitle1_y2,
                s=subtitle1_text2,
                size=subtitle_size2,
                ha=subtitle1_ha2,
                va=subtitle1_va2,
                # fontproperties=font_bold.prop,
                color=subtitle1_color,
                alpha=0.6,
            )

            logos = {'Manchester United': 'mu',
                     'Arsenal': 'ar',
                     'Aston Villa': 'av',
                     'Chelsea': 'ch',
                     'Liverpool': 'li',
                     'Manchester City': 'mc',
                     'Newcastle United': 'nu',
                     'Tottenham': 'th',
                     'West Ham': 'wh'}

            # Add team logo
            if team in logos.keys():
                image_path = f'images/{logos[team]}.png'
                image = Image.open(image_path)
                newax = fig2.add_axes([0, 0.855, 0.111, 0.111], anchor='W',
                                      zorder=1)
                newax.imshow(image)
                newax.axis('off')

            for i, ax in enumerate(axs2['pitch'].flat[:len(players)]):
                # Player names
                player_names = axs2['pitch'][i].text(
                    40, 126, players[i],
                    ha='center',
                    # va='center',
                    # weight='bold',
                    alpha=0.7,
                    fontsize=player_names_size,
                )

                # Data 1
                data_label = axs2['pitch'][i].text(
                    40, 121.5,
                    f'{player_events[players[i]]} Passes'
                    f' - {player_cmp[players[i]]}% Accuracy',
                    ha='center',
                    alpha=0.7,
                    # va='center',
                    fontsize=data1_size,
                )

                # ------------ Add 3rds Lines
                y, _ = standard.transform([1 / 3 * 100, 2 / 3 * 100], [0, 0])

                pitch_thirds2 = axs2['pitch'][i].hlines(
                    y=y,
                    xmin=-1,
                    xmax=81,
                    colors='black',
                    linestyles='dashed',
                    alpha=0.4,
                    clip_on=False,
                )

                # Pitch background color
                axs2['pitch'][i].set_facecolor(pitch_bg_color)

                # Unsuccessful Passes
                pdf = team_df[team_df['player'] == players[i]]
                pdf = pdf[pdf['outcome_type'] == 'Unsuccessful']
                xstart, ystart = standard.transform(pdf['x'], pdf['y'])
                xend, yend = standard.transform(pdf['end_x'], pdf['end_y'])

                pitch2.lines(
                    xstart=xstart,
                    ystart=ystart,
                    xend=xend,
                    yend=yend,
                    comet=is_line_transparent,
                    # color='#c1c1bf', # BenGriffis gray
                    color=event2_marker_color1,
                    ax=axs2['pitch'][i],
                    lw=event_line_width2,
                    label=f'{player_events[players[i]] - scc_player[players[i]]}'
                          f' missed',

                    transparent=is_line_transparent,
                    alpha_start=line_alpha_start2,
                    alpha_end=line_alpha_end2,
                )

                pitch2.scatter(
                    x=xend,
                    y=yend,
                    ax=axs2['pitch'][i],
                    s=event_marker_width2,
                    linewidth=0,
                    marker='o',
                    facecolor=event2_marker_color2,
                )

                # Successful Passes
                pdf = team_df[team_df['player'] == players[i]]
                pdf = pdf[pdf['outcome_type'] == 'Successful']
                xstart, ystart = standard.transform(pdf['x'], pdf['y'])
                xend, yend = standard.transform(pdf['end_x'], pdf['end_y'])

                pitch2.lines(
                    xstart=xstart,
                    ystart=ystart,
                    xend=xend,
                    yend=yend,
                    comet=True,
                    color=event1_marker_color1,
                    ax=axs2['pitch'][i],
                    lw=event_line_width2,
                    label=label_completed2,
                    transparent=is_line_transparent,
                    alpha_start=line_alpha_start2,
                    alpha_end=line_alpha_end2,
                )

                pitch2.scatter(
                    x=xend,
                    y=yend,
                    ax=axs2['pitch'][i],
                    s=event_marker_width2,
                    marker='o',
                    facecolor=event1_marker_color2,
                    # facecolor='#ef4146',
                    zorder=2,
                )

                # ------------ Add Legend
                # Trick to return handles and labels and show them in reversed order
                handles, labels = axs2['pitch'][i].get_legend_handles_labels()
                order = [1, 0]
                # legend = axs2['pitch'][i].legend(
                #     [handles[idx] for idx in order],
                #     [labels[idx] for idx in order],
                #     facecolor=legend_bg_color2,
                #     # reverse=True,
                #     # handlelength=5,
                #     edgecolor=legend_edge_color2,
                #     # prop=robotto_regular.prop,
                #     labelcolor=legend_text_color2,
                #     framealpha=legend_alpha2,
                #     loc=legend_ref2,
                #     bbox_to_anchor=legend_loc2,
                #     fontsize='large',
                # )

                legend_y = -5
                legend_completedt2 = axs2['pitch'][i].text(
                    x=40,
                    y=legend_y,
                    s=label_completed2(scc_player, players, i),
                    ha='center',
                    size=15,
                    color=event1_marker_color2,
                )

                legend_missed2 = axs2['pitch'][i].text(
                    x=40,
                    y=legend_y - 4.5,
                    s=label_missed2(player_events, scc_player, players, i),
                    ha='center',
                    size=15,
                    color=event2_marker_color2,
                )

            # ------------ Add Credits
            # Twitter Account
            tw_account = axs2['title'].text(
                1,
                .95,
                '@DGCFutbol',
                va='top',
                ha='right',
                fontsize=15.5,
                weight='bold',
                # ontproperties=robotto_regular.prop,
                # color='#941C2F',
                color=event1_marker_color1,
                alpha=1,
            )

            # Source label
            source = axs2['title'].text(
                1,
                .75,
                'Source: \'Opta Sports\'',
                va='top',
                ha='right',
                fontsize=13,
                # weight='bold',
                # ontproperties=robotto_regular.prop,
                color='#030303',
                # color=event1_marker_color1,
                alpha=0.7,
            )

            st.pyplot(fig2,
                      # use_container_width=False
                      )
    #
    # with tab_four:
    #
    #     st.caption('Note: This viz only uses the \'Team\' filter.')
    #
    #     fig, axs = plt.subplots(nrows=4, ncols=5, figsize=(20, 18), dpi=200)
    #     axs = np.array(axs)
    #
    #     for index, ax in enumerate(axs.reshape(-1)):
    #         pitch = plot_attacking(ax)
    #
    #     plt.subplots_adjust(
    #         left=0.05,
    #         right=0.95,
    #         bottom=0,
    #         wspace=.1,
    #         hspace=-0.5,
    #     )
    #
    #     # Title axes stretches fig to full width
    #     # dimensions(left, bottom, width, height) of new axes.
    #     # In fractions of fig w and h
    #     title_ax = fig.add_axes(
    #         [0, 0.8, 1, 0.1]
    #     )
    #
    #     title_ax.axis('off')
    #
    #     # Bottom-margin
    #     fig.text(
    #         x=0.5, y=0.09,
    #         s='o',
    #         c=fig_bg_color,
    #     )
    #
    #     title = title_ax.text(
    #         x=0.5, y=0.8,
    #         s="WHICH TEAMS ARE GETTING BETTER AT PROGRESSING THE BALL?",
    #         va="top", ha="center",
    #         fontsize=25,
    #         color="black",
    #         # font="DM Sans",
    #         weight="bold"
    #     )
    #
    #     # --------------------------- Filter Data
    #     # --- General filter for all 5 columns
    #
    #     # Filter by team
    #     pdf = df[df['team'] == team]
    #
    #     # Filter by Opposition
    #     pdf = pdf[
    #         ((pdf['home'] == team) & (pdf['away'].isin(rivals)))
    #         |
    #         ((pdf['home'].isin(rivals)) & (pdf['away'] == team))
    #         ]
    #
    #     # Passes only
    #     pdf = pdf[pdf['type'] == 'Pass']
    #
    #     # --- First Column - Passes into Final 3rd
    #     pdf1 = pdf[
    #         (pdf['end_x'] >= (2/3 * 100))
    #         & (pdf['end_x'] <= (3/3 * 100))
    #         ]
    #
    #     # --- Second Column - Carries into Final 3rd
    #     # --- Third Column - Passes into Pen Box
    #
    #     # Filter by penalty box coordinates
    #     sb_to_op = Standardizer(pitch_from='statsbomb', pitch_to='opta')
    #     endx, endy = sb_to_op.transform([102, 102], [18, 62])
    #     pdf3 = pdf[
    #         (
    #                 (pdf['end_x'] >= endx[0])
    #                 & (pdf['end_y'] >= endy[1])
    #                 & (pdf['end_y'] <= endy[0])
    #         )
    #         ]
    #
    #
    #     # --- Fourth Column - Carries into Pen Box
    #
    #     # --- Fifth Column - Passes in Pen Box
    #
    #     # --------------------------- Plot Events
    #
    #     # --- Third Column - Passes into Pen Box
    #     lw = 1
    #     mw1 = 1
    #
    #     # Get top 5 players with most  successful passes
    #     pdf_f = pdf3[pdf3['outcome_type'] == 'Successful']
    #     top = pdf_f[['player', 'type']].groupby(['player']).agg('count')
    #     print(top)
    #     top = top.sort_values(by=['type'], ascending=False).head().index.to_list()
    #
    #     for i, player in enumerate(top):
    #
    #         # Filter by player
    #         pdf = pdf3[pdf3['player'] == player]
    #         # Unsuccessful Passes
    #         pdfu = pdf[pdf['outcome_type'] == 'Unsuccessful']
    #         xstart, ystart = standard.transform(pdfu['x'], pdfu['y'])
    #         xend, yend = standard.transform(pdfu['end_x'], pdfu['end_y'])
    #
    #         axs[2][i].text(
    #             x=60, y=-5,
    #             s=f'{player}',
    #             ha='center',
    #             va='bottom'
    #         )
    #
    #         pitch.lines(
    #             xstart=xstart,
    #             ystart=ystart,
    #             xend=xend,
    #             yend=yend,
    #             comet=is_line_transparent,
    #             # color='#c1c1bf', # BenGriffis gray
    #             color=event2_marker_color1,
    #             ax=axs[2][i],
    #             lw=lw,
    #             label=f'55'
    #                   f' missed',
    #
    #             transparent=is_line_transparent,
    #             alpha_start=line_alpha_start2,
    #             alpha_end=line_alpha_end2,
    #         )
    #
    #         pitch.scatter(
    #             x=xend,
    #             y=yend,
    #             ax=axs[2][i],
    #             s=mw1,
    #             # linewidth=0,
    #             marker='o',
    #             facecolor=event2_marker_color1,
    #         )
    #
    #         # Successful Passes
    #         pdfs = pdf[pdf['outcome_type'] == 'Successful']
    #         xstart, ystart = standard.transform(pdfs['x'], pdfs['y'])
    #         xend, yend = standard.transform(pdfs['end_x'], pdfs['end_y'])
    #
    #         pitch.lines(
    #             xstart=xstart,
    #             ystart=ystart,
    #             xend=xend,
    #             yend=yend,
    #             comet=True,
    #             color=event1_marker_color1,
    #             ax=axs[2][i],
    #             lw=lw,
    #             label=f'50',
    #             transparent=is_line_transparent,
    #             alpha_start=line_alpha_start2,
    #             alpha_end=line_alpha_end2,
    #         )
    #
    #         pitch.scatter(
    #             x=xend,
    #             y=yend,
    #             ax=axs[2][i],
    #             s=mw1,
    #             marker='o',
    #             facecolor=event1_marker_color2,
    #             # facecolor='#ef4146',
    #             zorder=2,
    #         )

    # plt.savefig('filename.png',
    #             bbox_inches='tight',
    #             dpi=500
    #             )
    #
    # st.pyplot(fig2,
    #           # use_container_width=False
    #           )

    st.write('Instrucciones:\n'
             '1. Selecciona un Equipo\n'
             '2. Selecciona un Jugador\n'
             '3. Selecciona uno o mas rivales.\n\n'
             )

    st.divider()

    st.write(
        'Aquí hay un desglose de los pases de los jugadores seleccionados, y '
        'abajo se destacan los jugadores del equipo seleccionado que mas '
        'pases dieron. Podrían ser de interés.\n'
    )

    if team_events > 0:
        prec = round(scc_team / team_events * 100, 1)
    else:
        prec = 0.0

    passes_df = [
        {'Player': team,
         'Pases Totales': team_events,
         'Completados': scc_team,
         'Fallados': fail_team,
         'Precision (%)': prec}

    ]

    for i, pl in enumerate(players):
        passes_df.append(
            {'Player': pl,
             'Pases Totales': player_events[pl],
             'Completados': scc_player[pl],
             'Fallados': fail_player[pl],
             'Precision (%)': player_cmp[pl]
             }
        )

    st.write(pd.DataFrame(passes_df))

    st.write(top)

    st.divider()

    st.write('Instrucciones adicionales:\n\n'
             'Puedes cambiar los filtros de la barra lateral para mayor '
             'exploración de datos. Por ejemplo, puedes seleccionar solo 3 '
             'jugadores (quizás los 3 que mas pases dieron?) y seleccionar '
             'la pestana "Tres Jugadores".')

    st.divider()
