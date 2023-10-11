import pandas as pd
import streamlit as st

import plotly.express as px
import seaborn as sns

sns.set(style="ticks")

DEFAULT_LABEL_CONVERSION = {
    "bioactivity_class": "Bioactivity Class",
    "value": "pIC50"
}


def plot_bioactivity_class_frequency_px(df: pd.DataFrame) -> st.plotly_chart:
    fig = px.histogram(df, x="bioactivity_class", color="bioactivity_class",
                       labels=DEFAULT_LABEL_CONVERSION)
    fig.update_layout(xaxis_title="<b>Bioactivity Class</b>",
                      yaxis_title="<b>Frequency</b>",
                      title="<b>Distribution of Bioactivity Classes</b>")
    st.plotly_chart(fig, use_container_width=True)


def plot_pIC50_px(df: pd.DataFrame) -> st.plotly_chart:
    fig = px.histogram(df, x="pIC50", labels=DEFAULT_LABEL_CONVERSION)
    fig.update_layout(yaxis_title="<b>Number of Compounds</b>",
                      xaxis_title="<b>pIC50</b>",
                      title="<b>Distribution of Compounds by pIC50 Value</b>")
    st.plotly_chart(fig, use_container_width=True)


def boxplot_bioactivity_class_px(df: pd.DataFrame, y_axis: str
                                 ) -> st.plotly_chart:
    fig = px.box(df, x="bioactivity_class", y=y_axis, points="all",
                 labels=DEFAULT_LABEL_CONVERSION)
    fig.update_layout(yaxis_title="<b>" + y_axis + "</b>",
                      xaxis_title="<b>" + "Bioactivity Class" + "</b>")
    st.plotly_chart(fig)


def scatterplot_px(df, x_axis: str, y_axis: str, hue: str, size: str
                   ) -> st.plotly_chart:
    fig = px.scatter(df, x=x_axis, y=y_axis, color=hue, size=size,
                     color_discrete_sequence=px.colors.qualitative.Antique,
                     labels=DEFAULT_LABEL_CONVERSION)
    fig.update_layout(yaxis_title="<b>" + y_axis + "</b>",
                      xaxis_title="<b>" + x_axis + "</b>",
                      title=str(x_axis) + " vs " + str(y_axis))
    st.plotly_chart(fig)
