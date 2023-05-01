from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import plotly.express as px


class BatchDash:
    def __init__(self, name, df, check_col, x, y, color):
        app = DjangoDash(name, external_stylesheets=[dbc.themes.BOOTSTRAP])  # replaces dash.Dash

        app.layout = html.Div([
            dbc.Spinner(dcc.Graph(id="graph"), fullscreen=True, color="success"),
            dcc.Checklist(
                id="checklist",
                options=df[check_col].unique(),
                value=df[check_col].unique()[:1],
                inline=True,
                labelStyle={"margin": "10px"}
            ),
        ])

        @app.callback(
            Output("graph", "figure"),
            Input("checklist", "value"))
        def update_line_chart(values):
            mask = df[check_col].isin(values)
            fig = px.line(df[mask], x=x, y=y, color=color)
            return fig

