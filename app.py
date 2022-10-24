import re

from flask import Flask, jsonify, make_response, send_file
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import pandas as pd
import chardet
import re
import matplotlib.pyplot as plt
import numpy as np
import base64

fileKamus = 'resource/new_kamusalay.csv'
app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info = {
        'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
        'version': LazyString(lambda: '1.0.0'),
        'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling')
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
    "enableCORS": False,
}
swagger = Swagger(app, template=swagger_template,config=swagger_config)
@cross_origin()

@swag_from("docs/dataclean.yml", methods=['POST'])
@app.route('/dataclean', methods=['POST'])
def dataclean():
    if 'file' in request.files:   
        file = request.files['file']
        fileName = 'data.csv'
        file.save(fileName)
        dfFromFile = pd.read_csv(fileName, encoding=checkDataType(fileName), sep='~!~')
        cleanedData = []
        for index, row in dfFromFile.iterrows():
            cleanedRowText = cleanSlang(row['Tweet'])
            cleanedData.append(cleanedRowText)
        chartImage = createChart(dfFromFile)
        # response = make_response(send_file(chartImage,mimetype='image/png'))
        # response.headers['Content-Transfer-Encoding']='base64'
        # return response
        return jsonify({'text': '\n'.join(cleanedData), 'image': chartImage.decode('utf-8')})
    else:
        print(request.form)
        cleanedText = cleanSlang(request.form['textvalue'])
        return cleanedText

def cleanText(text):
    text = text.lower()
    text = text.strip()
    text = re.sub('\n', ' ', text)
    text = re.sub('[^0-9a-zA-Z]+', ' ', text)
    text = re.sub('user|rt', ' ', text)
    text = re.sub('x[a-z0-9]{2}', ' ', text)
    text = re.sub(' +', ' ', text)
    return text

def cleanSlang(text):
    text = cleanText(text)
    dfSlang = pd.read_csv(fileKamus, encoding=checkDataType(fileKamus))
    dicSlang = dict(zip(dfSlang.slang, dfSlang.formal))
    words = []
    for word in text.split(' '):
        if word in dicSlang.keys():
            word = dicSlang[word]
        words.append(word)
    return ' '.join(words)

def checkDataType(file):
    with open(fileKamus, 'rb') as rawdata:
        dataType = chardet.detect(rawdata.read(100000))
        return dataType['encoding']

def createChart(df):
    hateSpeech = df["HS"].tolist()
    countHateSpeech = pd.DataFrame(hateSpeech).sum()[0]

    abusive = df["Abusive"].tolist()
    countAbusive = pd.DataFrame(abusive).sum()[0]
    headers = ['hate_speech', 'abusive']
    values = [countHateSpeech, countAbusive]
    dfChart = pd.DataFrame({
        'Name': headers,
        'Point': values
    })
    dfChart.plot(x="Name", y="Point", kind="bar")
    plt.savefig('chart.png', bbox_inches='tight')
    return encodeFile('chart.png')

def encodeFile(fileName):
    with open(fileName, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string
if __name__ == '__main__':
    app.run()
