import boto3
import os
import vision_service
from PIL import Image
import io

aws_access_key_id = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

sqs = session.client(service_name='sqs', endpoint_url='https://message-queue.api.cloud.yandex.net',
                     aws_access_key_id=aws_access_key_id,
                     aws_secret_access_key=aws_secret_access_key,
                     region_name='ru-central1')

q_url = os.getenv("queue_url")


def handler(event, context):
    print(event)
    bucket_id = event['messages'][0]['details']['bucket_id']
    object_id = event['messages'][0]['details']['object_id']

    file = s3.get_object(Bucket=bucket_id, Key=object_id)['Body'].read()

    image = Image.open(io.BytesIO(file))

    face_detection = vision_service.detect_faces(file)
    if 'faces' not in face_detection:
        return 0
    crop_image(image, face_detection['faces'], bucket_id, object_id)


def crop_image(image, face_coords, bucket_id, object_id):
    for face_coord in face_coords:
        vertices = face_coord['boundingBox']['vertices']
        xleft = 0
        ytop = 0
        xright = 0
        ybottom = 0
        if 'x' in vertices[0]:
            xleft = vertices[0]['x']
        else:
            xleft = vertices[1]['x']
        if 'y' in vertices[0]:
            ytop = vertices[0]['y']
        else:
            ytop = vertices[3]['y']
        if 'x' in vertices[2]:
            xright = vertices[2]['x']
        else:
            xright = vertices[3]['x']
        if 'y' in vertices[1]:
            ybottom = vertices[1]['y']
        else:
            ybottom = vertices[2]['y']

        filename = "(" + xleft + "," + ytop + "," + xright + "," + ybottom + ")" + object_id
        print(filename)
        cropped_image = image.crop((int(xleft), int(ytop), int(xright), int(ybottom)))
        img_byte_arr = io.BytesIO()
        cropped_image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()
        s3.put_object(Bucket=bucket_id, Key=filename, Body=img_byte_arr, Metadata={'parent': object_id})

        sqs.send_message(QueueUrl=q_url, MessageBody=filename)


