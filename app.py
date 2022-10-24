import re
from flask import Flask, jsonify
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
import base64
import sqlite3

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
    #dfSlang = pd.read_csv(fileKamus, encoding=checkDataType(fileKamus))
    dfSlang = pd.read_sql_query("SELECT Slang, Formal from SlangDictionary", sqlConn())
    dicSlang = dict(zip(dfSlang.Slang, dfSlang.Formal))
    words = []
    for word in text.split(' '):
        if word in dicSlang.keys():
            word = dicSlang[word]
        words.append(word)
    newWords = cleanStopWord(' '.join(words))
    return newWords

def cleanStopWord(text):
    dfStopWord = pd.read_sql_query("SELECT Word from StopWords", sqlConn())
    listStopWord = dfStopWord["Word"].tolist()
    words = []
    for word in text.split(' '):
        if word not in listStopWord:
            words.append(word)
    return ' '.join(words)

def checkDataType(file):
    with open(file, 'rb') as rawdata:
        dataType = chardet.detect(rawdata.read(100000))
        return dataType['encoding']

def createChart(df):
    hateSpeech = df["HS"].tolist()
    countHateSpeech = pd.DataFrame(hateSpeech).sum()[0]

    abusive = df["Abusive"].tolist()
    countAbusive = pd.DataFrame(abusive).sum()[0]

    hsIndividual = df["HS_Individual"].tolist()
    countHsIndividual = pd.DataFrame(hsIndividual).sum()[0]

    hsGroup = df["HS_Group"].tolist()
    countHsGroup = pd.DataFrame(hsGroup).sum()[0]

    hsReligion = df["HS_Religion"].tolist()
    countHsReligion = pd.DataFrame(hsReligion).sum()[0]

    hsRace = df["HS_Race"].tolist()
    countHsRace = pd.DataFrame(hsRace).sum()[0]

    hsPhysical = df["HS_Physical"].tolist()
    countHsPhysical = pd.DataFrame(hsPhysical).sum()[0]

    hsGender = df["HS_Gender"].tolist()
    countHsGender = pd.DataFrame(hsGender).sum()[0]

    hsOther = df["HS_Other"].tolist()
    countHsOther = pd.DataFrame(hsOther).sum()[0]

    hsWeak = df["HS_Weak"].tolist()
    countHsWeak = pd.DataFrame(hsWeak).sum()[0]

    hsModerate = df["HS_Moderate"].tolist()
    countHsModerate = pd.DataFrame(hsModerate).sum()[0]

    hsStrong = df["HS_Strong"].tolist()
    countHsStrong = pd.DataFrame(hsStrong).sum()[0]

    headers = ['hate_speech', 'abusive', 'HS_Individual','HS_Group','HS_Religion','HS_Race','HS_Physical','HS_Gender','HS_Other','HS_Weak','HS_Moderate','HS_Strong']
    values = [countHateSpeech, countAbusive, countHsIndividual, countHsGroup, countHsReligion, countHsRace, countHsPhysical, countHsGender, countHsOther, countHsWeak, countHsModerate, countHsStrong ]
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

def sqlConn():
    con = sqlite3.connect("cleansing_db.db")
    return con

if __name__ == '__main__':
    app.run()
