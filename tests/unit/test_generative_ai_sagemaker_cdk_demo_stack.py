import aws_cdk as core
import aws_cdk.assertions as assertions

from stack.generative_ai_demo_web_stack import GenerativeAiDemoWebStack

# example tests. To run these tests, uncomment this file along with the example
# resource in generative_ai_sagemaker_cdk_demo/generative_ai_sagemaker_cdk_demo_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GenerativeAiDemoWebStack(app, "GenerativeAiDemoWebStack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
