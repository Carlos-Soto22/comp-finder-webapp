from flask import Flask, request, jsonify, render_template
import pandas as pd
from datetime import datetime
from utils import *

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("main.html")

@app.route("/search", methods=["POST"])
def search():
    address = request.json.get("address", "")

    if address is None:
        return jsonify({"table": "<div class='alert alert-warning'>Address cannot be empty.</div>"}), 400
    
    start_date = request.json.get("start_date", None)  # None if not provided
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()  # Convert to date if not None
    else:
        start_date = datetime(2023, 10, 1).date() 
    months = request.json.get("months", 6)
    radius = request.json.get("radius", 0.5)
    
    #df = get_comps(address)
    df = get_comps(address,start_date=start_date,months=months,radius=radius)
    if df is None:
        return jsonify({"table": "<div class='alert alert-info'>No df is none.</div>"})
    if isinstance(df, pd.DataFrame) and df.empty:
        return jsonify({"table": "<div class='alert alert-info'>No similadf is emptyound.</div>"})
    
    # Convert DataFrame to HTML
    html_table = df.to_html(classes="table table-striped", index=False)
    return jsonify({"table": html_table})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443)
