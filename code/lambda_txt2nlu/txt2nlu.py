import json
import boto3

runtime= boto3.client('runtime.sagemaker') 

MAX_LENGTH = 256
NUM_RETURN_SEQUENCES = 1
TOP_K = 35 # Has to be larger than zero
TOP_P = 0.7
DO_SAMPLE = True 

def lambda_handler(event, context):
    body = json.loads(event['body'])
    prompt = body['prompt']
    endpoint_name = body['endpoint_name']
    
    payload = {
        "inputs": prompt,
        "parameters":{
               "max_length": MAX_LENGTH, 
               "num_return_sequences": NUM_RETURN_SEQUENCES,
               "top_k": TOP_K,
               "top_p": TOP_P,
               "do_sample": DO_SAMPLE
        }
    }       
    payload = json.dumps(payload).encode('utf-8')
    
    response = runtime.invoke_endpoint(EndpointName=endpoint_name, 
                                  ContentType= 'application/json', 
                                  Body=payload)
    
    model_predictions = json.loads(response['Body'].read())
    generated_text = model_predictions[0]['generated_text']
    
    message = {"prompt": prompt,'generated_text':generated_text}
    
    return {
        "statusCode": 200,
        "body": json.dumps(message),
        "headers": {
            "Content-Type": "application/json"
        }
    }