
from flask import Flask, render_template, request
from utils.steam_api_client import resolve_and_filter_ids, fetch_inventory, get_profile_data
from utils.inventory_processor import process_inventory, QUALITY_COLORS

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    inventory_data = []
    error = None

    if request.method == "POST":
        input_ids = request.form["steam_ids"]
        steamids = resolve_and_filter_ids(input_ids)

        for steamid64 in steamids:
            try:
                profile = get_profile_data(steamid64)
                items = fetch_inventory(steamid64)
                processed_items = process_inventory(items)

                inventory_data.append({
                    "steamid": steamid64,
                    "profile": profile,
                    "items": processed_items
                })
            except Exception as e:
                error = str(e)

    return render_template("index.html", inventory_data=inventory_data, error=error, quality_colors=QUALITY_COLORS)

if __name__ == "__main__":
    app.run(debug=True)
