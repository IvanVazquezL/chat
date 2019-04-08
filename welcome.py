# -*- coding: utf-8 -*-
# Copyright 2018 IBM Corp. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the “License”)
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from dotenv import load_dotenv
from flask import Flask, Response
from flask import jsonify
from flask import request
from flask_socketio import SocketIO
from flask_cors import CORS
from watson_developer_cloud import ConversationV1
from watson_developer_cloud import SpeechToTextV1
from watson_developer_cloud import TextToSpeechV1

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'conversation' in vcap:
        conversationCreds = vcap['conversation'][0]['credentials']
        assistantUsername = conversationCreds.get('412cfe7b-db06-4bea-af43-40fc71ffc3b7')
        assistantPassword = conversationCreds.get('gx7gV0nJUL4c')
        #assistantIAMKey = conversationCreds.get('apikey')
        assistantUrl = conversationCreds.get('https://gateway.watsonplatform.net/conversation/api/v1/workspaces/79594e4d-2deb-4cb5-9c4d-f2ab0067250e/message')

    if 'text_to_speech' in vcap:
        textToSpeechCreds = vcap['text_to_speech'][0]['credentials']
        textToSpeechUser = textToSpeechCreds.get('74a05956-62ae-474e-98c8-5e9fb289a0df')
        textToSpeechPassword = textToSpeechCreds.get('qkiIuj6Jr5Dt')
        textToSpeechUrl = textToSpeechCreds.get('https://stream.watsonplatform.net/text-to-speech/api')
        #textToSpeechIAMKey = textToSpeechCreds.get('apikey')
    if 'speech_to_text' in vcap:
        speechToTextCreds = vcap['speech_to_text'][0]['credentials']
        speechToTextUser = speechToTextCreds.get('9cfb437d-1952-402b-b7b1-1c8a29bcb94f')
        speechToTextPassword = speechToTextCreds.get('4hHT7k3kFxlx')
        speechToTextUrl = speechToTextCreds.get('https://stream.watsonplatform.net/speech-to-text/api')
        #speechToTextIAMKey = speechToTextCreds.get('apikey')

    if "WORKSPACE_ID" in os.environ:
        workspace_id = os.getenv('79594e4d-2deb-4cb5-9c4d-f2ab0067250')

   # if "ASSISTANT_IAM_APIKEY" in os.environ:
        #assistantIAMKey = os.getenv('ASSISTANT_IAM_APIKEY')

else:
    print('Found local VCAP_SERVICES')
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    assistantUsername = os.environ.get('412cfe7b-db06-4bea-af43-40fc71ffc3b7')
    assistantPassword = os.environ.get('gx7gV0nJUL4c')
    #assistantIAMKey = os.environ.get('ASSISTANT_IAM_APIKEY')
    assistantUrl = os.environ.get('https://gateway.watsonplatform.net/conversation/api/v1/workspaces/79594e4d-2deb-4cb5-9c4d-f2ab0067250e/message')

    textToSpeechUser = os.environ.get('74a05956-62ae-474e-98c8-5e9fb289a0df')
    textToSpeechPassword = os.environ.get('qkiIuj6Jr5Dt')
    textToSpeechUrl = os.environ.get('https://stream.watsonplatform.net/text-to-speech/api')
    #textToSpeechIAMKey = os.environ.get('TEXTTOSPEECH_IAM_APIKEY')

    speechToTextUser = os.environ.get('9cfb437d-1952-402b-b7b1-1c8a29bcb94f')
    speechToTextPassword = os.environ.get('4hHT7k3kFxlx')
    workspace_id = os.environ.get('79594e4d-2deb-4cb5-9c4d-f2ab0067250e')
    speechToTextUrl = os.environ.get('https://stream.watsonplatform.net/speech-to-text/api')
    #speechToTextIAMKey = os.environ.get('SPEECHTOTEXT_IAM_APIKEY')


@app.route('/')
def Welcome():
    return app.send_static_file('index.html')


@app.route('/api/conversation', methods=['POST', 'GET'])
def getConvResponse():
    # Instantiate Watson Assistant client.
    # only give a url if we have one (don't override the default)
    try:
        assistant_kwargs = {
            'version': '2018-09-20',
            'username': '412cfe7b-db06-4bea-af43-40fc71ffc3b7',
            'password': 'gx7gV0nJUL4c',
            #'iam_apikey': assistantIAMKey,
            'url': 'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/79594e4d-2deb-4cb5-9c4d-f2ab0067250e/message'
        }

        assistant = AssistantV1(**assistant_kwargs)

        convText = request.form.get('convText')
        convContext = request.form.get('context')

        if convContext is None:
            convContext = "{}"
        jsonContext = json.loads(convContext)

        response = assistant.message(workspace_id='79594e4d-2deb-4cb5-9c4d-f2ab0067250e',
                                     input={'text': convText},
                                     context=jsonContext)
    except Exception as e:
        print(e)

    response = response.get_result()
    reponseText = response["output"]["text"]
    responseDetails = {'responseText': reponseText[0],
                       'context': response["context"]}
    return jsonify(results=responseDetails)


@app.route('/api/text-to-speech', methods=['POST'])
def getSpeechFromText():
    tts_kwargs = {
            'username': '74a05956-62ae-474e-98c8-5e9fb289a0df',
            'password': 'qkiIuj6Jr5Dt',
            #'iam_apikey': textToSpeechIAMKey,
            'url': 'https://stream.watsonplatform.net/text-to-speech/api'
    }

    inputText = request.form.get('text')
    ttsService = TextToSpeechV1(**tts_kwargs)

    def generate():
        audioOut = ttsService.synthesize(
            inputText,
            'audio/wav',
            'es-LA_SofiaVoice').get_result()

        data = audioOut.content

        yield data

    return Response(response=generate(), mimetype="audio/x-wav")


@app.route('/api/speech-to-text', methods=['POST'])
def getTextFromSpeech():
    tts_kwargs = {
            'username': '9cfb437d-1952-402b-b7b1-1c8a29bcb94f',
            'password': '4hHT7k3kFxlx',
            #'iam_apikey': speechToTextIAMKey,
            'url': 'https://stream.watsonplatform.net/speech-to-text/api'
    }

    sttService = SpeechToTextV1(**tts_kwargs)

    response = sttService.recognize(
            audio=request.get_data(cache=False),
            content_type='audio/wav',
            timestamps=True,
            word_confidence=True).get_result()

    text_output = response['results'][0]['alternatives'][0]['transcript']

    return Response(response=text_output, mimetype='plain/text')


port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(port))