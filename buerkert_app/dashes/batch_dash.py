from math import ceil as up

from dash import dcc, html, Input, Output, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import plotly.express as px


class BatchDash:
    def __init__(self, name, df, check_col, x, y, color):
        app = DjangoDash(name, external_stylesheets=[dbc.themes.BOOTSTRAP])  # replaces dash.Dash
        app.css.append_css({"external_url": "/static/buerkert_app/css/main.css"})
        page_size = 100

        app.layout = html.Div([
            dcc.Checklist(
                id="checklist",
                options=df[check_col].unique(),
                value=df[check_col].unique()[:1],
                inline=True,
                labelStyle={"margin": "10px"}
            ),
            dbc.Spinner(dcc.Graph(id="graph"), fullscreen=True, color="success"),
            html.Div([dbc.Button("Export Table", id="export_table", className="me-md-2")],
                     className="d-grid gap-2 d-md-flex justify-content-md-end mb-2"),
            dash_table.DataTable(df.to_dict('records'), id='batch_table', filter_action='native', export_format='xlsx',
                                 page_size=page_size,
                                 columns=[{"name": "Sensor-ID", "id": "sensor_id"},
                                          {"name": "Field", "id": "_field"},
                                          {"name": "Time", "id": "_time"},
                                          {"name": "Value", "id": "_value"}]),
            dbc.Pagination(id="pagination", max_value=up(df.shape[0] / page_size),
                           first_last=True, previous_next=True, fully_expanded=False,
                           className="justify-content-center mt-2"),
        ])

        app.clientside_callback(
            """
            function(n_clicks) {
                if (n_clicks > 0)
                    document.querySelector("#batch_table button.export").click()
                return ""
            }
            """,
            Output("export_table", "data-dummy"),
            [Input("export_table", "n_clicks")]
        )

        @app.callback(
            Output("batch_table", "page_current"),
            [Input("pagination", "active_page")],
        )
        def change_page(page):
            return page-1 if page else 1

        @app.callback(
            Output("graph", "figure"),
            Input("checklist", "value"))
        def update_line_chart(values):
            mask = df[check_col].isin(values)
            fig = px.line(df[mask], x=x, y=y, color=color)
            return fig

        @app.callback(
            Output("batch_table", "data"),
            Input("checklist", "value"))
        def update_line_chart(values):
            data = df[df["_field"].isin(values)]
            return data.to_dict('records')

        @app.callback(
            Output("pagination", "max_value"),
            Input("checklist", "value")
        )
        def change_pagingation(values):
            return up(df[df["_field"].isin(values)].shape[0]/page_size)

