import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.image as mpimg
from mplsoccer import Pitch, VerticalPitch
import io
import matplotlib.pyplot as plt
from PIL import Image
from urllib.request import urlopen


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

title_text2 = st.sidebar.text_input(
    label='2nd Figure Title',
    value=f'Chelsea Passes Into Final Third'
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

# ------------------------- COUNT DATA
# --- Dataframe with team events

# Count and get % of total
team_events = team_df.count()['player']
# Successful - Count
scc_team = team_df[team_df['outcome_type'] == 'Successful'].count()['player']
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
    p[player] = round(player_events[player] / team_events * 100, 1)

    # Successful - Count
    scc_player[player] = \
    player_df[player][team_df['outcome_type'] == 'Successful'].count()[
        'player']

    player_cmp[player] = round(
        scc_player[player] / player_events[player] * 100, 1)

    # Unsuccessful

    fail_player[player] = \
    player_df[player][team_df['outcome_type'] == 'Unsuccessful'].count()[
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
st.subheader('Type of Passes')

st.divider()

col1, col2 = st.columns(2)

# Count
with col1:
    st.text(
        f'Team passes: {team_events}\n'
        f'Successful: {scc_team}\n'
        f'Unsuccessful: {fail_team}\n'
    )
    for i, pl in enumerate(players):
        st.text(
            f'{pl}: {player_events[pl]} ({p[pl]}% of team)\n'
            f'Successful: {scc_player[pl]} ({player_cmp[pl]}% comp. rate)\n'
            f'Unsuccessful: {fail_player[pl]}'
        )
with col2:
    st.dataframe(top)

st.divider()

# ------------------------------ FORMAT PLOT ----------------------------------
# -------------------------- EDIT/CHANGE PARAMETERS

image_url = 'https://cdn5.wyscout.com/photos/team/public/25_120x120.png'

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
event1_marker_color1 = '#0b4393'
event2_marker_color1 = '#B5B4B2'
event_line_width1 = 1.8

event_marker_width1 = 12

is_line_transparent = True
line_alpha_start = 0.1
line_alpha_end = 1

# Legend
legend_ref = 'lower center'
legend_loc = (0.5, 0)  # Loc. of the lower center of the Legend
label1 = f'Completed passes = {scc_player[players[0]]}'
label2 = f'Missed passes = {player_events[players[0]] - scc_player[players[0]]}'

legend_bg_color = 'white'
legend_edge_color = 'black'
legend_text_color = 'black'
legend_alpha = 1

# --- Figure: Credits


# --------------------------- PLOT 2 PARAMETERS -------------------------------
# Title
title_size2 = 30

title_x2 = 0.089
title_y2 = 0.9
title_ha2 = 'left'
title_va2 = 'top'

# Subtitle
subtitle1_text2 = f'23/24 Premier League | As of Matchweek 12 | ' \
                  f'Top 3 Players with Most Attempted Passes Into Final 3rd'
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
tab_one, tab_two, tab_three, tab_four = st.tabs([
    "One Player",
    "Into Final 3rd",
    "Inside Final 3rd",
    "Attack",
]
)
with tab_one:
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
            color=event2_marker_color1,
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
            facecolor=event2_marker_color1,
        )

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
            color=event1_marker_color1,
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
    axs['pitch'].text(
        79,
        119,
        '@DGCFutbol',
        va='top',
        ha='right',
        fontsize=13,
        weight='bold',
        # ontproperties=robotto_regular.prop,
        color='#030303',
        alpha=0.3,
    )

    # DRAW FIG
    st.pyplot(fig)

# -------------------------- SETUP MULTIGRID FIGURE
with tab_two:
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
        pad_bottom=-8,
    )

    fig2, axs2 = pitch2.grid(
        nrows=1, ncols=len(players),
        figheight=10,

        title_height=0.15,  # the title takes up 15% of the fig height
        grid_height=0.7,  # the grid takes up 71.5% of the figure height
        endnote_height=0.00,  # endnote takes up 6.5% of the figure height

        grid_width=0.5,  # gris takes up 95% of the figure width

        # 1% of fig height is space between pitch and title
        title_space=0.035,

        # 1% of fig height is space between pitch and endnote
        endnote_space=0.01,

        space=0.05,  # 5% of grid_height is reserved for space between axes

        # centers the grid horizontally / vertically
        left=left_p,
        bottom=None,
        axis=False,
    )

    # Figure background color
    fig2.patch.set_facecolor(fig_bg_color)

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

    # Add team logo
    image = Image.open(urlopen(image_url))
    newax = fig2.add_axes([.065, 0.83, 0.111, 0.111], anchor='C', zorder=1)
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
        pitch_thirds = axs2['pitch'][i].hlines(
            y=[40, 80],
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
            color=event2_marker_color1,
            ax=axs2['pitch'][i],
            lw=event_line_width2,
            label=f'{player_events[players[i]] - scc_player[players[i]]}'
                  f' missed',

            transparent=is_line_transparent,
            alpha_start=line_alpha_start2,
            alpha_end=line_alpha_end2,
        )

        pitch.scatter(
            x=convert_x(xend),
            y=convert_y(yend),
            ax=axs2['pitch'][i],
            s=event_marker_width2,
            linewidth=0,
            marker='o',
            facecolor=event2_marker_color2,
        )

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
            color=event1_marker_color1,
            ax=axs2['pitch'][i],
            lw=event_line_width2,
            label=label_completed2,
            transparent=is_line_transparent,
            alpha_start=line_alpha_start2,
            alpha_end=line_alpha_end2,
        )

        pitch.scatter(
            x=convert_x(xend),
            y=convert_y(yend),
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

        legend_y = 32
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
