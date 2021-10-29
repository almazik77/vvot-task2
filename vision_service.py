import os
import base64
import requests
import json

vision_api_key = "Bearer " + os.getenv('vision_api_key')
folder_id = os.getenv("folder_id")


def encode_file(file):
    return base64.b64encode(file).decode('UTF-8')


def detect_faces(file):
    file_content = encode_file(file)
    body = json.dumps({
        'folderId': folder_id,
        'analyze_specs': [{
            'content': file_content,
            'features': [{
                'type': 'FACE_DETECTION'
            }]
        }]
    })
    headers = {
        "Authorization": vision_api_key
    }
    response = requests.post('https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze', data=body, headers=headers)
    print(response.json())
    return response.json()['results'][0]['results'][0]['faceDetection']
