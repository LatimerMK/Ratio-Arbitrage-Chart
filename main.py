import webview
from ui.template import HTML_CODE
from core.api import API

if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        'Ratio Arbitrage Chart v0.5.2',
        html=HTML_CODE,
        js_api=api,
        width=1280,
        height=750,
        background_color='#0d0f14'
    )
    webview.start(debug=True)


