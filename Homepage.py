import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
from mplsoccer import PyPizza, add_image, FontManager
import pandas as pd
import numpy as np

# ------------------------ Page config ----------------------------------------
st.set_page_config(
    page_title='Data Analysis',
    page_icon='EC'

)
# ------------------------- Functions -----------------------------------------


def map_stat_labels(labels_list):
    map_labels = {'Tackles\nplus\nInterceptions': 'Tackles +\nInterceptions',
                  'Percent\nof\nChallenge\nSuccess': 'Succ. Challenge %'}

    for i, label in enumerate(labels_list):
        if label in map_labels.keys():
            labels_list[i] = map_labels[label]

    return labels_list


def rank_data(stat_list, input_df, exclude_vals):
    vals = []
    debug = pd.DataFrame(input_df[['player', 'team', '90s']])

    for val in stat_list:
        ranks_df = pd.DataFrame(input_df[['player', 'team', '90s']])
        ranks_df.loc[:, val] = input_df[val]
        debug.loc[:, val] = input_df[val]
        # Eliminate columns with 0 on stat to be ranked
        ranks_df = ranks_df[ranks_df[val] != 0]
        # Filter out players with less than 450 mins
        ranks_df = ranks_df[ranks_df['90s'] >= 5]

        # Make stat p90 where applicable
        if val in exclude_vals:
            div = 1
        else:
            div = ranks_df['90s']

        ranks_df.loc[:, val] = ranks_df[val] / div

        # Calculate rank from available players
        ranks_df.loc[:, val] = round(ranks_df[val].rank(pct=True) * 100, 2)
        debug.loc[:, val] = ranks_df.loc[:, val]  # copy ranks to debug table
        # Store rank for selected player
        try:
            vals.append(ranks_df[val][ranks_df['player'] == player].iloc[0])

        except IndexError:
            vals.append(0)

    return vals, debug


@st.cache_data()
def read_csv(link):
    return pd.read_csv(link)


# ------------------- Read Database -------------------------------------------

df = read_csv('data/22-23_fbref_stats.csv')
# ----------------------------- DATA ------------------------------------------
# Percentiles
pizza = df

# fixtures.loc[:, 'Fecha'] = fixtures_date[0]
pizza = pizza.reset_index(drop=True)

# ------------------------------- LAYOUT --------------------------------------
# ------------------------------- Sidebar
st.sidebar.write('Hello')
st.sidebar.button('Press me')

# Content
st.header(':soccer: This is an app')

st.divider()

st.subheader('Ranks')

# -------------------------------- RANK LIST ----------------------------------
# CHOOSE VALUE TO RANK
exclude_values_p90 = ['Percent_of_Challenge_Success',
                      'Sh/90',
                      'SoT/90']

rv_df = df.iloc[:, 12:]  # Exclude categorical columns
ranked_vals = rv_df.select_dtypes(include=np.number).columns.tolist()

rank_val = st.selectbox('Rank by', ranked_vals, index=6)

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

# ------------------------- RANK PIZZA PLOT ------------------------------
pizza_rank = pd.DataFrame(df)
st.subheader('Rank bar plot')

# Tabs for stats select
tab_def, tab_poss, tab_atk = st.tabs(["Defense", "Possession", "Attack"])

with tab_def:
    # Choose defense stats for pizza plot
    with st.expander('Advanced Settings'):
        stats_def = st.multiselect(
            'Choose stats',
            ranked_vals,
            default=[
                'Tkl+Int',
                'TklWinPoss',
                'DrbTkl%',
                'AerialWin%',
                'Clr',
            ]
        )

with tab_poss:
    # Choose possession stats for pizza plot
    with st.expander('Advanced Settings'):
        stats_poss = st.multiselect(
            'Choose stats',
            ranked_vals,
            default=[
                'PassesAttempted',
                'TotCmp%',
                'LiveTouch',
                'ProgCarries',
                'Switches'
            ]
        )

with tab_atk:
    # Choose possession stats for pizza plot
    with st.expander('Advanced Settings'):
        stats_atk = st.multiselect(
            'Choose stats',
            ranked_vals,
            default=[
                'npxG',
                'SoT/90',
                'SCA90',
                'CarriesToPenArea',
                'ProgPassesRec'
            ]
        )

col1, col2 = st.columns(2)

with col1:
    # Filter by player
    player = st.selectbox('Choose Player',
                          pizza_rank.player.unique(),
                          index=20)
    # Player is filtered after calculating ranks

# # Create list of rank values for pizza chart
# rank_vals = []
# # For debugging table
# ranks_debug = pd.DataFrame(pizza_rank[['player', 'team', '90s']])
#
# for i, stat in enumerate(stats_def):
#     ranks = pd.DataFrame(pizza_rank[['player', 'team', '90s']])
#     ranks.loc[:, stat] = pizza_rank[stat]
#     ranks_debug.loc[:, stat] = pizza_rank[stat]
#     # Eliminate columns with 0 on stat to be ranked
#     ranks = ranks[ranks[stat] != 0]
#     # Filter out players with less than 450 mins
#     ranks = ranks[ranks['90s'] >= 5]
#
#     # Make stat p90 where applicable
#     if stat in exclude_values_p90:
#         div = 1
#     else:
#         div = ranks['90s']
#
#     ranks.loc[:, stat] = ranks[stat] / div
#
#     # Calculate rank from available players
#     ranks.loc[:, stat] = round(ranks[stat].rank(pct=True) * 100, 2)
#     ranks_debug.loc[:, stat] = ranks.loc[:, stat]  # copy ranks to debug table
#     # Store rank for selected player
#     try:
#         rank_vals.append(ranks[stat][ranks['player'] == player].iloc[0])
#
#     except IndexError:
#         rank_vals.append(0)

# Vals for pizza chart
rank_vals_def, ranks_debug = rank_data(stats_poss,
                                       pizza_rank,
                                       exclude_values_p90)
rank_vals_poss = rank_data(stats_poss, pizza_rank, exclude_values_p90)[0]
rank_vals_atk = rank_data(stats_atk, pizza_rank, exclude_values_p90)[0]


# Format labels for pizza plot
labels = [x.replace('_', '\n') for x in stats_def + stats_poss + stats_atk]
labels = map_stat_labels(labels)

# ---------------------- Plotting the Pizza Chart -----------------------------
n_def = len(rank_vals_def)
n_poss = len(rank_vals_poss)
n_atk = len(rank_vals_atk)
# color for the slices and text
# slice_colors = ["#1A78CF"] * 5 + ["#FF9300"] * 5 + ["#D70232"] * 5
slice_colors = ["#1A78CF"] * n_def + ["#FF9300"] * n_poss + ["#D70232"] * n_atk

# text_colors = ["#000000"] * 10 + ["#F2F2F2"] * 5
text_colors = ["#000000"] * (n_def + n_poss) + ["#F2F2F2"] * n_atk

baker = PyPizza(
    params=labels,
    background_color="#222222",  # background color
    straight_line_color="#000000",  # color for straight lines
    straight_line_lw=1,
    last_circle_lw=1,  # linewidth of last circle
    other_circle_lw=0,  # linewidth for other circles
    inner_circle_size=20  # size of inner circle

)

fig_pizza, ax = baker.make_pizza(
    values=rank_vals_def + rank_vals_poss + rank_vals_atk,
    figsize=(8, 8.5),  # adjust the figsize according to your need
    color_blank_space="same",  # use the same color to fill blank space
    slice_colors=slice_colors,  # color for individual slices
    value_colors=text_colors,  # color for the value-text
    value_bck_colors=slice_colors,  # color for the blank spaces
    blank_alpha=0.4,  # alpha for blank-space colors
    kwargs_slices=dict(
        edgecolor="#000000", zorder=2, linewidth=1
    ),  # values to be used when plotting slices
    kwargs_params=dict(
        color="#F2F2F2", fontsize=11,
        va='center',
        wrap=True
    ),  # values to be used when adding parameter labels
    kwargs_values=dict(
        color="#F2F2F2", fontsize=11,
        zorder=3,
        bbox=dict(
            edgecolor="#000000", facecolor="cornflowerblue",
            boxstyle="round,pad=0.2", lw=1
        )
    )  # values to be used when adding parameter-values labels
)

# add credits
CREDIT_1 = "data: statsbomb via fbref"
CREDIT_2 = "inspired by: @Worville, @FootballSlices, @somazerofc & @Soumyaj15209314"

fig_pizza.text(
    0.01, 0.02, f"{CREDIT_1}\n{CREDIT_2}", size=9,
    color="#F2F2F2",
    ha="left"
)

st.pyplot(fig_pizza)

st.dataframe(ranks_debug[['player'] + stats_def])

st.divider()

# ------------------------- PACHO BAR GRAPH TEST ------------------------------

import plotly.graph_objects as go

matches = ['SV Darmstadt', 'Mainz 05', 'FC Koln', 'VfL Vochum', 'SC Freiburg']
scores = [7.3, 8, 7.9, 7.6, 7.3]


fig_plotly = go.Figure()

fig_plotly.add_trace(go.Bar(x=matches,
                            y=scores,
                            text=scores,
                            textposition='inside',
                            )
                     )

fig_plotly.update_layout(
    title=dict(
        text='William Pacho - Bundesliga 23/24',
        automargin=True,
        font_size=25,
        y=0.9,
        x=0.5,
        xanchor='center',
        yanchor='top'),

    yaxis=dict(
        title="Puntaje Fotmob",
        title_font_size=18,
        range=[0, 10],
        showticklabels=False
    ),

    xaxis_tickfont_size=14,

    uniformtext_minsize=15,
    uniformtext_mode='hide',
)

st.plotly_chart(fig_plotly)
