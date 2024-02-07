import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.title = "THISuccess AI Studierende Analytics Dashboard"

server = app.server
app.config.suppress_callback_exceptions = True


app.layout = html.Div(
    id="app-container",
    children=[
        # Banner
        html.Div(
            id="banner",
            className="banner",
            children=[
                dcc.Link(
                    html.Img(src=app.get_asset_url("thi_logo_b_RGB.png"),
                             style={"width": "60px", "height": "auto", "margin-right": "10px"}),
                    href="/",
                ),
                html.Div(
                    [
                        dcc.Link(
                            f"{page['name']}",
                            href=page["relative_path"],
                            className="nav-button",
                        )
                        for page in dash.page_registry.values()
                    ],
                    className="nav-links",
                    style={"margin": "auto"},
                ),
            ],
            style={"background-color": "#f0f0f0", "display": "flex", "justify-content": "flex-start", "align-items": "center", "padding": "10px"},
        ),
        dash.page_container,
    ]
)

if __name__ == '__main__':
    app.run(debug=True)