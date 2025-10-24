import re
import wsgi  # uses the same app you run via `flask --app wsgi.py run`

def test_keys_loaded_before_main():
    client = wsgi.app.test_client()
    resp = client.get("/")
    html = resp.get_data(as_text=True)

    # Presence
    assert "js/keys.js" in html, "keys.js must be included on the base layout"
    assert "js/main.js" in html, "main.js must be included on the base layout"

    # Order: keys.js before main.js
    pos_keys = html.index("js/keys.js")
    pos_main = html.index("js/main.js")
    assert pos_keys < pos_main, "keys.js must be loaded before main.js"

    # (Optional) sanity: no duplicate script tags for main.js
    assert len(re.findall(r'js/main\.js', html)) == 1, "main.js should be included once globally"
