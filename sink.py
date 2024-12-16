from flask import Flask, request, jsonify, render_template, Response
from datetime import datetime
import csv
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point

app = Flask(__name__)

CSV_FILE = 'data.csv'

# Ensure CSV exists with headers
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "lat", "lng", "text"])

@app.route('/')
def home():
    # Main page with two buttons
    return render_template('index.html')

@app.route('/measure')
def measure():
    # Page to measure location and submit text
    return render_template('measure.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()
    location = data.get('location')
    text = data.get('text', '')
    if not location or not text:
        return jsonify({"error": "Missing location or text"}), 400

    lat = location.get('lat')
    lng = location.get('lng')

    # Append data to CSV
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), lat, lng, text])

    return jsonify({"message": "OK"}), 200

@app.route('/view', methods=['GET'])
def view_data():
    # Load CSV and show on map
    if not os.path.isfile(CSV_FILE):
        # If no data yet, just show empty
        return render_template('view.html', map="", table="")

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return render_template('view.html', map="", table="")

    # Rename columns to match what the map code expects
    # Original snippet expects: id, date, notes, longitude, latitude
    # We have: timestamp, lat, lng, text
    df = df.rename(columns={
        'timestamp': 'date', 
        'lat': 'latitude', 
        'lng': 'longitude', 
        'text': 'notes'
    })

    # Add an ID column
    df.insert(0, 'id', range(1, len(df) + 1))

    # Create geometry
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)

    # Create a map figure
    fig = px.scatter_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        hover_data=['id', 'date', 'notes'],
        zoom=10,
        height=600
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    # Create a table figure
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                   fill_color='paleturquoise',
                   align='left'),
        cells=dict(values=[df[col] for col in df.columns],
                  fill_color='lavender',
                  align='left'))
    ])

    map_html = fig.to_html(full_html=False)
    table_html = table_fig.to_html(full_html=False)

    return render_template('view.html', map=map_html, table=table_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
