from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin
import json

from snow_maps import create_snow_map, get_bbox

app = Flask(__name__)
CORS(app)

@app.route('/getmap')
def plot_image():
    params = request.args.get("params")

    parsed_params = json.loads(params)

    snow_image = create_snow_map(parsed_params, get_bbox("northeast"))

    return send_file(snow_image, mimetype="image/png")

@app.route('/hello')
def say_hello():
    return 'Hello!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')