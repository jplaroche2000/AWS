# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License. A copy of the
# License is located at
#
# http://aws.amazon.com/apache2.0/
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import os
import boto3
import email
import re
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

region = os.environ['Region']

def get_message_from_s3(message_id):

    incoming_email_bucket = os.environ['MailS3Bucket']
    incoming_email_prefix = os.environ['MailS3Prefix']

    if incoming_email_prefix:
        object_path = (incoming_email_prefix + "/" + message_id)
    else:
        object_path = message_id

    object_http_path = (f"http://s3.console.aws.amazon.com/s3/object/{incoming_email_bucket}/{object_path}?region={region}")

    # Create a new S3 client.
    client_s3 = boto3.client("s3")

    # Get the email object from the S3 bucket.
    object_s3 = client_s3.get_object(Bucket=incoming_email_bucket, Key=object_path)
    # Read the content of the message.
    file = object_s3['Body'].read()

    file_dict = {
        "file": file,
        "path": object_http_path
    }

    return file_dict


def send_email(message):
    aws_region = os.environ['Region']

    # Create a new SES client.
    client_ses = boto3.client('ses', region)

    # Send the email.
    try:
        #Provide the contents of the email.
        response = client_ses.send_raw_email(
            Source=message['Source'],
            Destinations=[
                message['Destinations']
            ],
            RawMessage={
                'Data':message['Data']
            }
        )

    # Display an error if something goes wrong.
    except ClientError as e:
        output = e.response['Error']['Message']
    else:
        output = "Email sent! Message ID: " + response['MessageId']

    return output

def lambda_handler(event, context):
    # Get the unique ID of the message. This corresponds to the name of the file
    # in S3.
    message_id = event['Records'][0]['ses']['mail']['messageId']
    print(f"Received message ID {message_id}")

    # Retrieve the file from the S3 bucket.
    file_dict = get_message_from_s3(message_id)

    msg = email.message_from_string(file_dict['file'].decode('utf-8'))
 
    original_sender = msg['From']
    print('original_sender: ' + original_sender)
    authorized_sender = os.environ['MailFrom']
    print('authorized_sender: ' + authorized_sender)
    msg.replace_header("From", authorized_sender)

    original_recipient = msg['To']
    print('original_recipient: ' + original_recipient)
    new_recipient = os.environ['MailRecipient']
    print('new_recipient: ' + new_recipient)
    msg.replace_header("To", new_recipient)
    
    # otherwise blocked by SES
    msg.replace_header("Return-Path", '<' + authorized_sender + '>')

    msg.replace_header("Subject", 'FW (' + original_sender + '): ' + msg['Subject'])
    msg.add_header('X-AWS-S3-Bucket', file_dict['path'])
    msg.add_header('X-AWS-SES-From', original_sender)
    msg.add_header('X-AWS-SES-To', original_recipient)

    
    message = {
        "Source": authorized_sender,
        "Destinations": new_recipient,
        "Data": msg.as_string()
    }

    # Send the email and print the result.
    result = send_email(message)
    print(result)
