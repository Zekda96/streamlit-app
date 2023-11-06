import streamlit as st
import pandas as pd
import numpy as np

# ------------------------ Page config ----------------------------------------
st.set_page_config(
    page_title='Data Analysis',
    page_icon=':soccer:'

)
# ------------------------- Functions -----------------------------------------


# def map_stat_labels(labels_list):
#     map_labels = {'Tackles\nplus\nInterceptions': 'Tackles +\nInterceptions',
#                   'Percent\nof\nChallenge\nSuccess': 'Succ. Challenge %'}
#
#     for i, label in enumerate(labels_list):
#         if label in map_labels.keys():
#             labels_list[i] = map_labels[label]
#
#     return labels_list


# def rank_data(stat_list, input_df, exclude_vals):
#     vals = []
#     debug = pd.DataFrame(input_df[['player', 'team', '90s']])
#
#     for val in stat_list:
#         ranks_df = pd.DataFrame(input_df[['player', 'team', '90s']])
#         ranks_df.loc[:, val] = input_df[val]
#         debug.loc[:, val] = input_df[val]
#         # Eliminate columns with 0 on stat to be ranked
#         ranks_df = ranks_df[ranks_df[val] != 0]
#         # Filter out players with less than 450 mins
#         ranks_df = ranks_df[ranks_df['90s'] >= 5]
#
#         # Make stat p90 where applicable
#         if val in exclude_vals:
#             div = 1
#         else:
#             div = ranks_df['90s']
#
#         ranks_df.loc[:, val] = ranks_df[val] / div
#
#         # Calculate rank from available players
#         ranks_df.loc[:, val] = round(ranks_df[val].rank(pct=True) * 100, 2)
#         debug.loc[:, val] = ranks_df.loc[:, val]  # copy ranks to debug table
#         # Store rank for selected player
#         try:
#             vals.append(ranks_df[val][ranks_df['player'] == player].iloc[0])
#
#         except IndexError:
#             vals.append(0)
#
#     return vals, debug


@st.cache_data()
def read_csv(link):
    return pd.read_csv(link)


# ------------------- Read Database -------------------------------------------
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
st.sidebar.write('Hello')
st.sidebar.button('Press me')

# Content
st.header(':soccer: This is an app')

st.divider()

st.subheader('Ranks')

# -------------------------------- RANK LIST ----------------------------------
# CHOOSE VALUE TO RANK
if 'exclude_values_p90' not in st.session_state:
    st.session_state['exclude_values_p90'] = ['Percent_of_Challenge_Success',
                                              'Sh/90',
                                              'SoT/90'
                                              ]

exclude_values_p90 = st.session_state['exclude_values_p90']

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
