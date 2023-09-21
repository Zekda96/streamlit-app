import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
from mplsoccer import PyPizza, add_image, FontManager
import pandas as pd
import numpy as np
# ----------------------------- Functions -------------------------------------------


def map_stat_labels(labels_list):
    map_labels = {'Tackles\nplus\nInterceptions': 'Tackles +\nInterceptions',
                  'Percent\nof\nChallenge\nSuccess': 'Succ. Challenge %'}

    for i, label in enumerate(labels_list):
        if label in map_labels.keys():
            labels_list[i] = map_labels[label]

    return labels_list


# ----------------------------- Read Database -------------------------------------------
# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)


# Perform SQL query on the Google Sheet.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_resource(ttl=600)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = pd.DataFrame(rows.fetchall())
    return rows


sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

# ----------------------------- DATA -------------------------------------------
# Percentiles
pizza = rows
pizza.reset_index(drop=True)


# -------------------------------------- COMPONENTS ------------------------------

# ---------------------------- PIZZA DATA


# ----------------------------------------------------- LAYOUT ---------------------------------------------------------
# --------------------------------------------- Sidebar
st.sidebar.write('Hello')
st.sidebar.button('Press me')

# Content
st.header(':soccer: This is an app')

st.divider()

st.subheader('Ranks')

# ---------------------------------------------- RANK LIST
# CHOOSE VALUE TO RANK
exclude_values_p90 = ['Percent_of_Challenge_Success']
exclude_from_rank = ['Season', 'Age', 'Born', 'Nineties']  # Columns to exclude from ranking

rv_df = rows.loc[:, ~rows.columns.isin(exclude_from_rank)]
ranked_vals = rv_df.select_dtypes(include=np.number).columns.tolist()

rank_val = st.selectbox('Rank by', ranked_vals, index=6)

# Eliminate columns with 0 on stat to be ranked
pizza = pizza[pizza[rank_val] != 0]

# Make stat p90 where applicable
if rank_val in exclude_values_p90:
    div = 1
else:
    div = rows['Nineties']

pizza.loc[:, rank_val] = rows[rank_val]/div

col1, col2, col3 = st.columns(3)
with col1:
    # FILTER BY POSITION
    pos_val = st.multiselect('Choose position', rows['Position'].unique(), default=['DF'])
    pizza = pizza[pizza['Position'].isin(pos_val)]

with col2:
    # FILTER BY 90s
    z1, z2 = st.select_slider(
        'Select 90s',
        options=sorted(rows.Nineties.unique()),
        value=(np.median(rows.Nineties.unique()), np.max(rows.Nineties.unique())))
    pizza = pizza[(pizza['Nineties'] >= z1) & (pizza['Nineties'] <= z2)]


# Display rank table
cols_to_show = ['Player', 'Team', 'Nineties', rank_val, 'Rank']

pizza['Rank'] = round(pizza[rank_val].rank(pct=True)*100, 0)
pizza.reset_index()
st.dataframe(pizza[cols_to_show].sort_values('Rank', ascending=False))

st.divider()

# ------------------------------------------------------- RANK BAR PLOT
bar_rank = pd.DataFrame(rows)
st.subheader('Rank bar plot')

# Tabs for stats select
tab1, tab2, tab3 = st.tabs(["Defense", "Possession", "Attack"])

with tab1:
    # Choose stats for pizza plot
    with st.expander('Advanced Settings'):
        stats = st.multiselect('Choose stats', ranked_vals, default=ranked_vals[1:])

col1, col2 = st.columns(2)

with col1:
    # Filter by player
    player = st.selectbox('Choose Player', bar_rank.Player.unique(), index=0)
    # Filter player at time of plotting

# Create dataframe to add ranks
ranks_list = []
ranks_df = pd.DataFrame(bar_rank[['Player', 'Team', 'Nineties']])  # For debugging table

for i, stat in enumerate(stats):
    ranks_temp_df = pd.DataFrame(bar_rank[['Player', 'Team', 'Nineties']])
    ranks_temp_df.loc[:, stat] = bar_rank[stat]
    ranks_df.loc[:, stat] = bar_rank[stat]
    # Eliminate columns with 0 on stat to be ranked
    ranks_temp_df = ranks_temp_df[ranks_temp_df[stat] != 0]
    # Filter out players with less than 450 mins
    ranks_temp_df = ranks_temp_df[ranks_temp_df['Nineties'] >= 5]

    # Make stat p90 where applicable
    if stat in exclude_values_p90:
        div = 1
    else:
        div = ranks_temp_df['Nineties']

    ranks_temp_df.loc[:, stat] = ranks_temp_df[stat] / div

    # Calculate rank from available players
    ranks_temp_df.loc[:, stat] = round(ranks_temp_df[stat].rank(pct=True) * 100, 2)
    ranks_df.loc[:, stat] = round(ranks_temp_df[stat].rank(pct=True) * 100, 2)
    # Store rank for selected player
    try:
        ranks_list.append(ranks_temp_df[stat][ranks_temp_df['Player'] == player].iloc[0])

    except IndexError:
        ranks_list.append(0)


# Labels for plot
labels = [x.replace('_', '\n') for x in stats]
labels = map_stat_labels(labels)

# ---------------------------- Plot Pizza Chart

# color for the slices and text
# slice_colors = ["#1A78CF"] * 5 + ["#FF9300"] * 5 + ["#D70232"] * 5
slice_colors = ["#1A78CF"] * 15
# text_colors = ["#000000"] * 10 + ["#F2F2F2"] * 5
text_colors = ["#000000"] * 15

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
    values=ranks_list,
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
CREDIT_1 = "data: statsbomb viz fbref"
CREDIT_2 = "inspired by: @Worville, @FootballSlices, @somazerofc & @Soumyaj15209314"

fig_pizza.text(
    0.01, 0.02, f"{CREDIT_1}\n{CREDIT_2}", size=9,
    color="#F2F2F2",
    ha="left"
)

st.pyplot(fig_pizza)

st.dataframe(ranks_df[['Player'] + stats])


st.divider()

# -------------------------------------------------------- EXAMPLE CODE
val = st.selectbox('Choose col', rows.columns.unique())
st.write(rows[val].unique())

st.divider()

options = st.multiselect('Choose values', rows.columns)
st.write(f'You will plot: {options}')

st.divider()

agree = st.toggle('Wanna check more?')
if agree:
    st.write('Great!')
    st.write(f"Here are stats for {rows.iloc[83].Player}")
    with st.expander('Open Oven'):
        st.pyplot(fig=fig_pizza)
