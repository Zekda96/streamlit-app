import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
import io


# ------------------------------- FUNCTIONS  ----------------------------------
def convert_x(vals):
    """ mplsoccer Pitch has dimensions x=120 and y=80 (Statsbomb)
    Current used scrapped data from WhoScored shows coordinates as
    percentages of the total length of the pitch, so x=100 and y=100.
    This converts WhoScored coordinates so they match mplsoccer's Pitch """

    if type(vals) is list:
        return_list = []
        for v in vals:
            return_list.append((v / 100) * 120)
        return return_list
    else:
        return (vals / 100) * 120


def convert_y(vals):
    """ mplsoccer Pitch has dimensions x=120 and y=80 (Statsbomb)
    Current used scrapped data from WhoScored shows coordinates as
    percentages of the total length of the pitch, so x=100 and y=100.
    This converts WhoScored coordinates so they match mplsoccer's Pitch """

    if type(vals) is list:
        return_list = []
        for v in vals:
            return_list.append((100 - v) / 100 * 80)
        return return_list
    else:
        return (100 - vals) / 100 * 80


# -------------------------------- LOAD DATA ----------------------------------
df = pd.read_csv('data/2324.csv')
df = df.iloc[:, 1:]

# ------------------------------- DASHBOARD  ----------------------------------
# ---------------------------- SIDEBAR FILTERS --------------------------------

# Selectbox to highlight team
team = st.sidebar.selectbox(
    label='Select teams',
    options=df.team.sort_values().unique(),
    index=int(np.where(df.team.sort_values().unique() == 'Chelsea')[0][0]),
)

# Selectbox to choose players of interest
players = st.sidebar.multiselect(
    label='Select players',
    options=df[df['team'] == team].player.dropna().sort_values().unique(),
    default='Enzo Fernández',
)

# Filter by actions against opposing team
# Local teams when away is the team of interest PLUS
# away teams when local is team of interest
rivals_opt = df.loc[df['home'] == team, 'away'].unique().tolist()
rivals_opt += df.loc[df['away'] == team, 'home'].unique().tolist()
rivals_opt.sort()
rivals = st.sidebar.multiselect(
    label='Select rivals',
    options=rivals_opt,
    default=['Liverpool']
)

# Filter by type of event
event = st.sidebar.selectbox(
    label='Choose event',
    options=['Pass', 'Shot'],
    # options=df.type.unique(),
)

if event == 'Pass':
    # Granular filter by pitch length
    l1, l2 = st.sidebar.select_slider(
        label='Select Pass Length (m)',
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
    'Filter by Starting Pitch Zone',
    options=np.arange(start=0, stop=121, step=1),
    value=(40, 80),
)

# Filter by Receiving Pitch Zone
end_x1, end_x2 = st.sidebar.select_slider(
    'Filter by Receiving Pitch Zone',
    options=np.arange(start=0, stop=121, step=1),
    value=(80, 120),
)

title_text = st.sidebar.text_input(
    label='Figure Title',
    value=f'{players[0]} Passes'
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
# Filter by type of event
plot_df = plot_df[plot_df['type'] == event]

# Length filtering occurs at after the length slider code as that slider
# is conditional and might not appear all the time.
# Filtering pseudo-code for reference;
# and (df['length'] >= l1) and (df['length'] <= l2)

# Filter by Starting Pitch Zone
plot_df = plot_df[
    (plot_df['x'] >= (x1 / 120 * 100))
    & (plot_df['x'] <= (x2 / 120 * 100))
]

# Filter by Receiving Pitch Zone
plot_df = plot_df[
    (plot_df['end_x'] >= (end_x1 / 120 * 100))
    & (plot_df['end_x'] <= (end_x2 / 120 * 100))
]

# Dataframe used for showing table and for multi-player plot
team_df = plot_df[['player', 'type', 'outcome_type',
                   'x', 'y', 'end_x', 'end_y']]
# FILTERING BY PLAYER IS DONE LAST SO WE CAN GET THE FILTERED DF OF ALL PLAYERS
# Filter by player
plot_df = plot_df[plot_df['player'].isin(players)]


# ------------------------ DATA FILTERING FOR COUNTING
# Dataframe with only player events
player_df = team_df[team_df['player'] == players[0]]

# Count and get % of total
team_events = team_df.count()['player']
player_events = player_df.count()['player']
p = round(player_events / team_events * 100, 1)

# Successful - Count
scc_team = team_df[team_df['outcome_type'] == 'Successful'].count()['player']
scc_player = player_df[team_df['outcome_type'] == 'Successful'].count()[
    'player']
player_cmp = round(scc_player/player_events * 100, 1)

# Unsuccessful
fail_team = team_df[team_df['outcome_type'] == 'Unsuccessful'].count()[
    'player']
fail_player = player_df[team_df['outcome_type'] == 'Unsuccessful'].count()[
    'player']

# ------------------ SORT TOP 5 PLAYERS
top = team_df[['player', 'type']].groupby(['player']).agg('count')
top = top.sort_values(by=['type'], ascending=False).head()

# ------------------------------- MAIN PAGE  ----------------------------------

# # Load fonts
# font_normal = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/roboto/Roboto%5Bwdth,wght%5D.ttf')
# font_italic = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/roboto/Roboto-Italic%5Bwdth,wght%5D.ttf')
# font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/
# main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf')

st.title('Chalkboard')
st.subheader('Passes into Final 3rd')

st.divider()

# Count

st.text(
    f'Team passes: {team_events}\n'
    f'{players[0]}: {player_events} ({p}% of team)\n'

    f'\nSuccessful\n'
    f'Team: {scc_team}\n'
    f'{players[0]}: {scc_player} ({player_cmp}% comp. rate)\n'

    f'\nUnsuccessful\n'
    f'Team: {fail_team}\nPLayer: {fail_player}'
)

st.dataframe(top)

st.divider()

# ------------------------------ FORMAT PLOT ----------------------------------
# -------------------------- EDIT/CHANGE PARAMETERS

# Figure
# Pitch Padding
pitch_left_pad = 0
pitch_right_pad = 0
pitch_top_ad = 0
# pitch_bottom_pad = 0
pitch_bottom_pad = -35

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
endnote_h = 0  # endnote takes up 6.5% of the figure height

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

subtitle1_text = f"23/24 Season | Premier League | As of Matchweek 12"

subtitle1_color = "#030303"

# - Subtitle2
subtitle2_x = 0.5
subtitle2_y = 0.2
subtitle2_ha = 'center'
subtitle2_va = 'center'
subtitle2_size = 10

subtitle2_text = f"23/24 | League only | Last 5 Matches | As of Nov 25, 2023"
subtitle2_color = "#030303"

# --- Figure: Pitch
pitch_line_width = 0.8
pitch_line_color = '#03191E'
pitch_bg_color = '#faf9f4'

# Events
event_marker_color1 = 'b'
event_marker_color2 = '#B5B4B2'
event_line_width1 = 3

event_marker_width1 = 12

is_line_transparent = True
line_alpha_start = 0.1
line_alpha_end = 1

# Legend
legend_ref = 'lower center'
legend_loc = (0.5, 0)  # Loc. of the lower center of the Legend
label1 = f'Completed passes = {scc_player}'
label2 = f'Missed passes = {player_events - scc_player}'

legend_bg_color = 'white'
legend_edge_color = 'black'
legend_text_color = 'black'
legend_alpha = 1

# --- Figure: Credits

# ----------------------------- SETUP FIGURE
pitch = VerticalPitch(
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
    # figheight=10,

    title_height=title_h,  # the title takes up 15% of the fig height
    grid_height=grid_h,  # the grid takes up 71.5% of the figure height
    endnote_height=endnote_h,  # endnote takes up 6.5% of the figure height
    #
    grid_width=grid_w,  # gris takes up 95% of the figure width
    #
    # # 1% of fig height is space between pitch and title
    title_space=title_space,
    #
    # # 1% of fig height is space between pitch and endnote
    endnote_space=endnote_space,
    #
    space=space,  # 5% of grid_height is reserved for space between axes
    #
    # # centers the grid horizontally / vertically
    left=left_p,
    bottom=None,
    axis=False,
)


# ------------ Add 3rds Lines
axs['pitch'].hlines(
    y=[40, 80],
    xmin=-3,
    xmax=83,
    colors='black',
    linestyles='dashed',
    alpha=0.5,
    clip_on=False,
)

# Figure background color
fig.patch.set_facecolor(fig_bg_color)
# Pitch background color
axs['pitch'].set_facecolor(pitch_bg_color)

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

    # Successful Passes
    pdf = plot_df[plot_df['outcome_type'] == 'Successful']
    xstart = pdf['x']
    ystart = pdf['y']
    xend = pdf['end_x']
    yend = pdf['end_y']

    pitch.lines(
        xstart=convert_x(xstart),
        ystart=convert_y(ystart),
        xend=convert_x(xend),
        yend=convert_y(yend),
        comet=True,
        color=event_marker_color1,
        ax=axs['pitch'],
        lw=event_line_width1,
        label=label1,
        transparent=is_line_transparent,
        alpha_start=line_alpha_start,
        alpha_end=line_alpha_end,
    )

    pitch.scatter(
        x=convert_x(xend),
        y=convert_y(yend),
        ax=axs['pitch'],
        s=event_marker_width1,
        marker='o',
        facecolor=event_marker_color1,
    )

    # Unsuccessful Passes
    pdf = plot_df[plot_df['outcome_type'] == 'Unsuccessful']
    xstart = pdf['x']
    ystart = pdf['y']
    xend = pdf['end_x']
    yend = pdf['end_y']

    pitch.lines(
        xstart=convert_x(xstart),
        ystart=convert_y(ystart),
        xend=convert_x(xend),
        yend=convert_y(yend),
        comet=is_line_transparent,
        # color='#c1c1bf', # BenGriffis gray
        color=event_marker_color2,
        ax=axs['pitch'],
        lw=event_line_width1,
        label=label2,
        transparent=is_line_transparent,
        alpha_start=line_alpha_start,
        alpha_end=line_alpha_end,
    )

    pitch.scatter(
        x=convert_x(xend),
        y=convert_y(yend),
        ax=axs['pitch'],
        s=event_marker_width1,
        linewidth=0,
        marker='o',
        facecolor=event_marker_color2,
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
axs['pitch'].text(
    79,
    119,
    '@DGCFutbol',
    va='top',
    ha='right',
    fontsize=12,
    # ontproperties=robotto_regular.prop,
    color='#030303',
    alpha=0.3,
)

# DRAW FIG
st.pyplot(fig)


# ----------------------- SETUP MULTIGRID FIGURE
pitch2 = VerticalPitch(
    # axis=True,
    # label=True,
    # tick=True,
    goal_type='box',
    line_color=pitch_line_color,
    # line_alpha=0.5,
    linewidth=pitch_line_width*2,

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
    figheight=20,

    title_height=0.06,  # the title takes up 15% of the fig height
    grid_height=0.8,  # the grid takes up 71.5% of the figure height
    endnote_height=0.03,  # endnote takes up 6.5% of the figure height

    grid_width=0.5,  # gris takes up 95% of the figure width

    # 1% of fig height is space between pitch and title
    title_space=0.05,

    # 1% of fig height is space between pitch and endnote
    endnote_space=0.05,

    space=0.05,  # 5% of grid_height is reserved for space between axes

    # centers the grid horizontally / vertically
    left=left_p,
    bottom=None,
    axis=False,
)

# Figure background color
fig2.patch.set_facecolor(fig_bg_color)

for i, ax in enumerate(axs2['pitch'].flat[:len(players)]):

    # plot the title below the pitches
    ax.text(40, -5, players[i],
            ha='center', va='center', fontsize=50,
            )

    # ------------ Add 3rds Lines
    axs2['pitch'][i].hlines(
        y=[40, 80],
        xmin=-1,
        xmax=81,
        colors='black',
        linestyles='dashed',
        alpha=0.5,
        clip_on=False,
    )

    # Pitch background color
    axs2['pitch'][i].set_facecolor(pitch_bg_color)

    # Successful Passes
    pdf = team_df[team_df['player'] == players[i]]
    pdf = pdf[pdf['outcome_type'] == 'Successful']
    xstart = pdf['x']
    ystart = pdf['y']
    xend = pdf['end_x']
    yend = pdf['end_y']

    pitch.lines(
        xstart=convert_x(xstart),
        ystart=convert_y(ystart),
        xend=convert_x(xend),
        yend=convert_y(yend),
        comet=True,
        color=event_marker_color1,
        ax=axs2['pitch'][i],
        lw=event_line_width1,
        label=label1,
        transparent=is_line_transparent,
        alpha_start=line_alpha_start,
        alpha_end=line_alpha_end,
    )

    pitch.scatter(
        x=convert_x(xend),
        y=convert_y(yend),
        ax=axs2['pitch'][i],
        s=event_marker_width1,
        marker='o',
        facecolor=event_marker_color1,
    )

    # Unsuccessful Passes
    pdf = team_df[team_df['player'] == players[i]]
    pdf = pdf[pdf['outcome_type'] == 'Unsuccessful']
    xstart = pdf['x']
    ystart = pdf['y']
    xend = pdf['end_x']
    yend = pdf['end_y']

    pitch.lines(
        xstart=convert_x(xstart),
        ystart=convert_y(ystart),
        xend=convert_x(xend),
        yend=convert_y(yend),
        comet=is_line_transparent,
        # color='#c1c1bf', # BenGriffis gray
        color=event_marker_color2,
        ax=axs2['pitch'][i],
        lw=event_line_width1,
        label=label2,
        transparent=is_line_transparent,
        alpha_start=line_alpha_start,
        alpha_end=line_alpha_end,
    )

    pitch.scatter(
        x=convert_x(xend),
        y=convert_y(yend),
        ax=axs2['pitch'][i],
        s=event_marker_width1,
        linewidth=0,
        marker='o',
        facecolor=event_marker_color2,
    )

    # ------------ Add Legend
    legend = axs2['pitch'][i].legend(
        facecolor=legend_bg_color,
        # handlelength=5,
        edgecolor=legend_edge_color,
        # prop=robotto_regular.prop,
        labelcolor=legend_text_color,
        framealpha=legend_alpha,
        loc=legend_ref,
        bbox_to_anchor=legend_loc,
        fontsize='xx-large',
    )

st.pyplot(fig2,
          # use_container_width=False
          )