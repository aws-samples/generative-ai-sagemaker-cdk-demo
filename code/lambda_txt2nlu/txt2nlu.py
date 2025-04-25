import json
import boto3

runtime = boto3.client('runtime.sagemaker') 

MAX_LENGTH = 512
NUM_RETURN_SEQUENCES = 1
TOP_K = 40
TOP_P = 0.8
DO_SAMPLE = True 
MAX_TOTAL_TOKENS = 512  # Maximum total tokens allowed by the model
MAX_CHARACTERS = 1700   # Maximum characters allowed in input

def truncate_input(prompt, max_tokens):
    # Truncate to MAX_CHARACTERS if the input is longer
    if len(prompt) > MAX_CHARACTERS:
        return prompt[:MAX_CHARACTERS]
    return prompt

def lambda_handler(event, context):
    body = json.loads(event['body'])
    prompt = body['prompt']
    endpoint_name = body['endpoint_name']
    
    # Truncate input if necessary
    max_input_tokens = MAX_TOTAL_TOKENS - MAX_LENGTH
    truncated_prompt = truncate_input(prompt, max_input_tokens)
    
    payload = {
        "inputs": truncated_prompt,
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
    
    message = {
        "prompt": truncated_prompt,
        "original_prompt": prompt,
        "was_truncated": prompt != truncated_prompt,
        'generated_text': generated_text
    }
    
    return {
        "statusCode": 200,
        "body": json.dumps(message),
        "headers": {
            "Content-Type": "application/json"
        }
    }