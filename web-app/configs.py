import boto3

region_name = boto3.Session().region_name

key_txt2img_api_endpoint = "txt2img_api_endpoint" # this value is from GenerativeAiDemoWebStack
key_txt2img_sm_endpoint = "txt2img_sm_endpoint"   # this value is from GenerativeAiTxt2ImgSagemakerStack

key_txt2nlu_api_endpoint = "txt2nlu_api_endpoint" # this value is from GenerativeAiDemoWebStack
key_txt2nlu_sm_endpoint = "txt2nlu_sm_endpoint"   # this value is from GenerativeAiTxt2nluSagemakerStack

def get_parameter(name):
    """
    This function retrieves a specific value from Systems Manager"s ParameterStore.
    """     
    ssm_client = boto3.client("ssm",region_name=region_name)
    response = ssm_client.get_parameter(Name=name)
    value = response["Parameter"]["Value"]
    
    return value