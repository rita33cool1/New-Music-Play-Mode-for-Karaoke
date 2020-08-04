from __future__ import print_function
import boto3
import os
import sys
import uuid
import operator
#from PIL import Image
#import PIL.Image



def lambda_handler(event, context):
    queue_name = 'karaoke-face-recognition'
    #for i in range(30):
    #    receive_sqs(queue_name)
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key'] 
        print('key:', key)
        try:
            direct, group_name, file_name = parse_key(key)
        except:
            print('parse key error')
        else:
            collection_id = '106062600_' + group_name
            create_collection(collection_id)
    
            if direct == '':
                save_data(bucket, key, collection_id)
            elif direct == 'unknown':        
                match_face = recognize(key, collection_id, bucket)
    
                topic_url = 'https://sqs.us-east-1.amazonaws.com/661664929584/karaoke-face-recognition'
                msg = group_name + '-' + match_face
                sqs_publish(topic_url, msg)
                
                #receive_sqs(queue_name)
                
def create_collection(collection):
    client = boto3.client('rekognition')

    try:
        response = client.create_collection(
            CollectionId=collection
        )
    except:
        print('create_collection error')

def parse_key(key):
    num = 0
    num = key.count('/')
    if num == 0:
        direct = ''
        latter = key
    else:
        direct, latter = key.split('/', 1)
    group_name, latter = latter.split('_', 1)
    latter = latter + 't'
    t, file_name = latter[::-1].split('gpj.', 1)
    print('file name: ', file_name[::-1])

    return (direct, group_name, file_name[::-1])

def save_data(bucket, key, collection_id):
    direct, group_name, image_id = parse_key(key)

    for record in index_faces(bucket, key, collection_id, image_id):
        face = record['Face']
        print ("Face ({}%)".format(face['Confidence']))
        print ("  FaceId: {}".format(face['FaceId']))
        print ("  ImageId: {}".format(face['ImageId']))


"""
    Expected output:
    Face (99.945602417%)
      FaceId: dc090f86-48a4-5f09-905f-44e97fb1d455
      ImageId: f974c8d3-7519-5796-a08d-b96e0f2fc242
"""



def index_faces(bucket, key, collection_id, image_id=None, attributes=(), region="us-east-1"):
    rekognition = boto3.client("rekognition", region)
    response = rekognition.index_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        ExternalImageId=image_id,
        DetectionAttributes=attributes,
    )
    return response['FaceRecords']

def recognize(key, collection_id, bucket):
    
    faces = []
    try:
        for record in search_faces_by_image(bucket, key, collection_id):
            face = record['Face']
            print ("Matched Face ({}%)".format(record['Similarity']))
            print ("  FaceId : {}".format(face['FaceId']))
            print ("  ImageId : {}".format(face['ExternalImageId']))
            similarity = float("{}".format(record['Similarity']))
            image = "{}".format(face['ExternalImageId'])
            print('similarity: ', similarity)
            print('image: ', image)
            
            faces.append((image, similarity))
    except:
        image_id = 'Unknown'
        print('No matched face')
    else:
        faces.sort(key=operator.itemgetter(1), reverse=True)
        image_id = faces[0][0]
        print('matched face: ', image_id)    

    return image_id 

"""
    Expected output:
    Matched Face (96.6647949219%)
      FaceId : dc090f86-48a4-5f09-905f-44e97fb1d455
      ImageId : test.jpg
"""

def search_faces_by_image(bucket, key, collection_id, threshold=80, region="us-east-1"):
    rekognition = boto3.client("rekognition", region)
    response = rekognition.search_faces_by_image(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        FaceMatchThreshold=threshold,
    )
    return response['FaceMatches']

def sns_publish(topic, msg):
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=topic,
        Message=msg,
    )
    
# Publish face name through SNS
def sqs_publish(topic_url,msg):
    # Create sqs client
    client = boto3.client('sqs')
    # Send message
    response = client.send_message(
        QueueUrl = topic_url,
        MessageBody = msg,
        DelaySeconds=0
    )

def receive_sqs(queue_name):
    # Get the service resource
    sqs = boto3.resource('sqs')

    # Get the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    # Process messages by printing out body and optional author name
    for message in queue.receive_messages(MessageAttributeNames=['Author']):
        # Get the custom author message attribute if it was set
        author_text = ''
        if message.message_attributes is not None:
            author_name = message.message_attributes.get('Author').get('StringValue')
            if author_name:
                author_text = ' ({0})'.format(author_name)
        
        # Print out the body and author (if set)
        print('Receive message: {0}!{1}'.format(message.body, author_text))

        # Let the queue know that the message is processed
        message.delete()
        
        # Check message content
        if '{0}'.format(message.body) == 'image uploaded':
            return True
        else: 
            return False