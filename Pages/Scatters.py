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


# -------------------------------- DATA ---------------------------------------
df = st.session_state['database']
# ------------------------------- LAYOUT --------------------------------------
# ------------------------------ Sidebar

# Filter by 90s played
z1, z2 = st.sidebar.select_slider(
    'Select 90s',
    options=sorted(df['90s'].unique()),
    value=(np.median(df['90s'].unique()), np.max(df['90s'].unique()))
)

# Selectbox to choose x value
val_x = st.sidebar.selectbox(
    label='Choose value for x axis',
    options=df.columns.values[12:],
    index=int(np.where(df.columns.values[12:] == 'npxG')[0][0])
)

# Selectbox to choose y value
val_y = st.sidebar.selectbox(
    label='Choose value for y axis',
    options=df.columns.values[12:],
    index=int(np.where(df.columns.values[12:] == 'CarriesToFinalThird')[0][0])
)

# Radio to select trendline or zones to scatterplot
graph_trend = st.sidebar.radio(
    label='Add to plot',
    options=['Trend line', 'Zones']

)

# Selectbox to choose type of zone lines
if graph_trend == 'Zones':
    zone_lines_type = st.sidebar.selectbox(
        label='Type of Zone Lines',
        options=['Median', 'Average'],
        index=1,
    )


df = df[(df['90s'] >= z1) & (df['90s'] <= z2)]

# ------------------------------ Content
st.header(':soccer: Scatter plots')

st.divider()

st.subheader('Choose x and y pairs')


# ------------------------------ Scatter 1 ------------------------------------
# val_x = 'npxG'
# val_y = 'CarriesToFinalThird'
df = make_p90(df, val_x)
df = make_p90(df, val_y)

fig = px.scatter(
    df,
    x=val_x,
    y=val_y,
    # customdata=np.stack([df['player']]),
    # name=customdata[0],
    hover_name='player',
)

fig = fig.update_traces(
    marker_size=10,
    marker_color='white',
    marker_line_width=1,
    marker_line_color='blue',
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

fig.update_layout(
    title_text='Scatter plot',
    title_font_size=30,
    title_automargin=True,
)

st.plotly_chart(fig)
