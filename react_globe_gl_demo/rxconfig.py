import reflex as rx

config = rx.Config(
    app_name="react_globe_gl_demo",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=rx.theme(appearance="dark", accent_color="cyan", radius="large")),
    ],
)
