import boto3
region = 'us-east-1'
instances = ['i-0cb8cd88bce342e12', 'i-021665495a9ff0cdf', 'i-0db46507caa5b64ce']
ec2 = boto3.client('ec2', region_name=region)
arn = 'arn:aws:sns:us-east-1:837962483194:LambdaExecutionTopic'

def lambda_handler(event, context):
    message = 'stopped your instance(s): ' + str(instances)
    ec2.stop_instances(InstanceIds=instances)
    print(message)
    client = boto3.client('sns')
    response = client.publish(
       TargetArn=arn,
       Message=message,
       MessageStructure='string'
    )
