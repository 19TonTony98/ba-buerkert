from enum import IntEnum
from math import ceil as up

import pandas as pd
from django.contrib import messages
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, dash_table, State
from django_plotly_dash import DjangoDash
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from buerkert.settings import DATABASES
from res.units import Units

RESOLUTION_RANGE = ['1s', '10s', '30s', '1m', '10m', '30m', '1h']


class BatchDash:
    def __init__(self, name, request, batch_id):
        self.request = request
        self.batch_id = batch_id
        check_col = "_field"
        x = "_time"
        y = "_value"
        color = 'sensor_id'

        if not (size := self.get_influx_size()):
            raise InfluxDBError(message=f"Keine Daten mit der Batch-ID {self.batch_id} gefunden")
        slider_value = min(((len(RESOLUTION_RANGE) - 1), int(size/7500)))
        df = self.get_influx_df(RESOLUTION_RANGE[slider_value])
        tb = df.copy()
        tb["unit"] = tb.apply(lambda row: getattr(Units, row['_field']).choice()[1], axis=1)

        app = DjangoDash(name, external_stylesheets=[dbc.themes.BOOTSTRAP])  # replaces dash.Dash
        app.css.append_css({"external_url": "/static/buerkert_app/css/main.css"})
        page_size = 100

        app.layout = html.Div([
            dcc.Checklist(
                id="checklist",
                options=units_resolve(df[check_col].unique()),
                value=df[check_col].unique()[:1],
                inline=True,
                labelStyle={"margin": "10px"}
            ),
            html.Div([
                html.Div("Auflösung", className="px-3"),
                dcc.Slider(marks={idx: value for idx, value in enumerate(RESOLUTION_RANGE)},
                           id='resolution-slider', min=0, max=len(RESOLUTION_RANGE) - 1, step=1, value=slider_value, ),
            ]),
            dbc.Spinner(dcc.Graph(id="graph"), fullscreen=True, color="success"),
            html.Div([dbc.Button("Zeige Tabelle", id="collapse_table", className="me-md-2", n_clicks=0),
                      dbc.Button("Export Tabelle", id="export_table", className="me-md-2")],
                     className="d-grid gap-2 d-md-flex justify-content-md-end mb-2 pt-2"),
            dbc.Collapse([dash_table.DataTable(tb.to_dict('records'), id='batch_table', filter_action='native',
                                               export_format='xlsx',
                                               page_size=page_size,
                                               columns=[{"name": "Sensor-ID", "id": "sensor_id"},
                                                        {"name": "Sensor-Name", "id": "display"},
                                                        {"name": "Einheit", "id": "unit"},
                                                        {"name": "Zeitstempel", "id": "_time"},
                                                        {"name": "Wert", "id": "_value"}]),
                          dbc.Pagination(id="pagination", max_value=up(tb.shape[0] / page_size),
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
            [Input("checklist", "value"),
             Input("resolution-slider", "value")])
        def update_line_chart(values, resolution):
            df = self.get_influx_df(RESOLUTION_RANGE[resolution])
            fig = go.Figure()
            layout_dict = {}
            for i, value in enumerate(values, 1):
                v_name = f"({getattr(Units, value).value[0]})" if len(values) > 1 else ""
                for group_name, group_df in df.loc[df[check_col] == value].groupby(color):
                    fig.add_trace(
                        go.Scatter(x=group_df[x], y=group_df[y], name=f"{group_name}{v_name}", yaxis=f"y{i}"))
                    fig['data'][-1]['showlegend'] = True
                f_col = px.colors.sequential.Rainbow[i]
                layout_dict[f"yaxis{i}"] = {"title": getattr(Units, value).value[1],
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
            data = tb[tb["_field"].isin(values)]
            return data.to_dict('records')

        @app.callback(
            Output("pagination", "max_value"),
            Input("checklist", "value")
        )
        def change_pagination(values):
            return up(tb[tb["_field"].isin(values)].shape[0] / page_size)

        @app.callback(
            [Output("collapseTable", "is_open"), Output("collapse_table", "children")],
            [Input("collapse_table", "n_clicks")],
            [State("collapseTable", "is_open")],
        )
        def toggle_collapse(n, is_open):
            label = "Zeige Tabelle" if is_open else "Verberge Tabelle"
            if n:
                return not is_open, label
            return is_open, "Zeige Tabelle"


    def get_influx_df(self, resolution="1m"):
        with InfluxDBClient(**DATABASES["influx"]) as client:
            query_api = client.query_api()
            query = f"""from(bucket: "{DATABASES["influx"]["bucket"]}")
                          |> range(start: 0)
                          |> filter(fn: (r) => r._measurement == "{self.batch_id}")
                          |> aggregateWindow(every: {resolution}, fn: mean, createEmpty: false)
                          |> yield(name: "mean")
                     """

            return query_api.query_data_frame(query)

    def get_influx_size(self):
        with InfluxDBClient(**DATABASES["influx"]) as client:
            query_api = client.query_api()
            query = f"""from(bucket: "{DATABASES["influx"]["bucket"]}") 
                        |> range(start: 0) 
                        |> filter(fn: (r) => r._measurement == "{self.batch_id}")
                        |> count()
                        """
            if result := query_api.query(query):
                return result[0].records[0].values['_value']


def units_resolve(units):
    return {getattr(Units, unit).name: getattr(Units, unit).value[0] for unit in units}
