import random
import uuid
from math import ceil as up

from dash import dcc, html, Input, Output, dash_table, State
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go


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
            html.Div([dbc.Button("Zeige Tabelle", id="collapse_table", className="me-md-2", n_clicks=0),
                      dbc.Button("Export Tabelle", id="export_table", className="me-md-2")],
                     className="d-grid gap-2 d-md-flex justify-content-md-end mb-2"),
            dbc.Collapse([dash_table.DataTable(df.to_dict('records'), id='batch_table', filter_action='native',
                                               export_format='xlsx',
                                               page_size=page_size,
                                               columns=[{"name": "Sensor-ID", "id": "sensor_id"},
                                                        {"name": "Field", "id": "_field"},
                                                        {"name": "Time", "id": "_time"},
                                                        {"name": "Value", "id": "_value"}]),
                          dbc.Pagination(id="pagination", max_value=up(df.shape[0] / page_size),
                                         first_last=True, previous_next=True, fully_expanded=False,
                                         className="justify-content-center mt-2"),
                          ],
                         id="collapseTable", is_open=False
                         )
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
            return page - 1 if page else 1

        @app.callback(
            Output("graph", "figure"),
            Input("checklist", "value"))
        def update_line_chart(values):
            fig = go.Figure()
            layout_dict = {}
            for i, value in enumerate(values, 1):
                v_name = value if len(values) > 1 else ""
                for group_name, group_df in df.loc[df[check_col] == value].groupby(color):
                    fig.add_trace(
                        go.Scatter(x=group_df[x], y=group_df[y], name=f"{group_name}({v_name})", yaxis=f"y{i}"))
                f_col = px.colors.sequential.Rainbow[i]
                layout_dict[f"yaxis{i}"] = {"title": v_name,
                                            "titlefont": {"color": f_col},
                                            "tickfont": {"color": f_col},
                                            "side": "left" if i % 2 else "right", }
                if i > 1:
                    layout_dict[f"yaxis{i}"].update({"overlaying": "y"})
            fig.update_layout(**layout_dict)
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
            return up(df[df["_field"].isin(values)].shape[0] / page_size)

        @app.callback(
            [Output("collapseTable", "is_open"), Output("collapse_table", "children")],
            [Input("collapse_table", "n_clicks")],
            [State("collapseTable", "is_open")],
        )
        def toggle_collapse(n, is_open):
            label = "Zeige Tabelle" if is_open else "Verberge Tabelle"
            if n:
                return not is_open, label
            return is_open, label
