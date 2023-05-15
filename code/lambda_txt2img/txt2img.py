import json
import boto3
runtime= boto3.client('runtime.sagemaker') 


def lambda_handler(event, context):
    body = json.loads(event['body'])
    prompt = body['prompt']
    endpoint_name = body['endpoint_name']
    
    response = runtime.invoke_endpoint(EndpointName=endpoint_name, 
                                      Body=prompt, 
                                      ContentType='application/x-text')    
    
    response_body = json.loads(response['Body'].read().decode())
    generated_image = response_body['generated_image']
    
    message = {"prompt": prompt,'image':generated_image}
    
    return {
        "statusCode": 200,
        "body": json.dumps(message),
        "headers": {
            "Content-Type": "application/json"
        }
    }