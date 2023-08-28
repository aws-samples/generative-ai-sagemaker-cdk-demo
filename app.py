#!/usr/bin/env python3
import aws_cdk as cdk

from stack.generative_ai_vpc_network_stack import GenerativeAiVpcNetworkStack
from stack.generative_ai_demo_web_stack import GenerativeAiDemoWebStack
from stack.generative_ai_txt2nlu_sagemaker_stack import GenerativeAiTxt2nluSagemakerStack
from stack.generative_ai_txt2img_sagemaker_stack import GenerativeAiTxt2imgSagemakerStack

from script.sagemaker_uri import *
import boto3

region_name = boto3.Session().region_name
env={"region": region_name}

#Text to Image model parameters
TXT2IMG_MODEL_ID = "model-txt2img-stabilityai-stable-diffusion-v2-1-base"
TXT2IMG_INFERENCE_INSTANCE_TYPE = "ml.p3.2xlarge" #if your region does not support this instance type, try ml.g4dn.4xlarge 
TXT2IMG_MODEL_TASK_TYPE = "txt2img"
TXT2IMG_MODEL_INFO = get_sagemaker_uris(model_id=TXT2IMG_MODEL_ID,
                                        model_task_type=TXT2IMG_MODEL_TASK_TYPE, 
                                        instance_type=TXT2IMG_INFERENCE_INSTANCE_TYPE,
                                        region_name=region_name)

#Text to NLU image model parameters
TXT2NLU_MODEL_ID = "huggingface-text2text-flan-t5-xl"
TXT2NLU_INFERENCE_INSTANCE_TYPE = "ml.g4dn.4xlarge" 
TXT2NLU_MODEL_TASK_TYPE = "text2text"
TXT2NLU_MODEL_INFO = get_sagemaker_uris(model_id=TXT2NLU_MODEL_ID,
                                        model_task_type=TXT2NLU_MODEL_TASK_TYPE,
                                        instance_type=TXT2NLU_INFERENCE_INSTANCE_TYPE,
                                        region_name=region_name)

app = cdk.App()

network_stack = GenerativeAiVpcNetworkStack(app, "GenerativeAiVpcNetworkStack", env=env)
GenerativeAiDemoWebStack(app, "GenerativeAiDemoWebStack", vpc=network_stack.vpc, env=env)

GenerativeAiTxt2nluSagemakerStack(app, "GenerativeAiTxt2nluSagemakerStack", env=env, model_info=TXT2NLU_MODEL_INFO)
GenerativeAiTxt2imgSagemakerStack(app, "GenerativeAiTxt2imgSagemakerStack", env=env, model_info=TXT2IMG_MODEL_INFO)

app.synth()
