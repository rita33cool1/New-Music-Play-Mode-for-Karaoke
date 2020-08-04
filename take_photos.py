#!/usr/bin/env python3

#import time
import boto3
#import face_recognition
#from os import listdir
#from os.path import isfile, join
from picamera import PiCamera
from time import sleep
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import socket
import ssl

group_file = './group.txt'
topic = 'karaoke/face'
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

# Publish face name through SNS
def sqs_publish(face):
    # Create sqs client
    client = boto3.client('sqs')
    # Send message
    response = client.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/073539042065/result',
        MessageBody='Name: '+face,
        DelaySeconds=0
    )
    


# Publish face name through SNS
def sns_publish(face):
    # create sns client
    client = boto3.client('sns')
    # Send message 
    response = client.publish(
        TopicArn='arn:aws:sns:us-east-1:073539042065:result_from_recognition',
        Message='Name: '+face,
    )


def s3_upload(mybucket, group_id, image):
    key = 'unknown/' + group_id + '_unknown.jpg'
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(image, mybucket, key)
    print('Uploaded image', key)

def take_photo(path):
    camera = PiCamera()
    
    camera.start_preview()
    camera.capture(path)
    camera.stop_preview()
    camera.close()

# Callback
def customCallback(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")
    group = str(payload) 
    print('Topic: '+topic+' Payload: '+group)
    with open(group_file, 'w') as f:
        f.write(group)

def IoT_publish(sub_topic):
    
    # Configuration
    host = 'a179b8updnd9vh.iot.us-east-1.amazonaws.com'
    rootCAPath = './Certification.pem'
    certificatePath = './ab112e152d-certificate.pem.crt'
    privateKeyPath = './ab112e152d-private.pem.key'
    clientId = '1'
    topic = sub_topic

    print('start')

    myAWSIoTMQTTClient = None
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, 8883)

    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    # Connect and Subscribe
    try: 
        myAWSIoTMQTTClient.connect(1000)
    except:
        print('Connect fail')
    else:
        print('Connect successfully')
        if myAWSIoTMQTTClient.subscribe(topic, 1, customCallback):
            return True
    return False

def get_group():
    with open(group_file, 'r') as f:
        group = f.readlines()
        #num = group[0].count('\n')
        group = group[0].rstrip()
    return group

def main():
#    image = '/home/pi/Desktop/tmp/test.jpg'
#    # Take photo
#    take_photo(image)

    group = get_group()
    while True:
        if IoT_publish(topic):
            print(group)
            group = get_group()
        image = '/home/pi/Desktop/tmp/test.jpg'
        # Take photo
        take_photo(image)
        # Upload image to S3 bucket
        mybucket = 'cloud-face-recognition'
        s3_upload(mybucket, group, image)
        sleep(15)
if __name__ == "__main__":
    main()
