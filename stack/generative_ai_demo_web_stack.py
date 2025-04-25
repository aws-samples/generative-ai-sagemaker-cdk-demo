from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ec2 as ec2,    
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_autoscaling as autoscaling,
)
from constructs import Construct

class GenerativeAiDemoWebStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Defines role for the AWS Lambda functions
        role = iam.Role(self, "Gen-AI-Lambda-Policy", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"))
        role.attach_inline_policy(iam.Policy(self, "sm-invoke-policy",
            statements=[iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:InvokeEndpoint"],
                resources=["*"]
            )]
        ))
        
        # Defines an AWS Lambda function for Image Generation service
        lambda_txt2img = _lambda.Function(
            self, "lambda_txt2img",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("code/lambda_txt2img"),
            handler="txt2img.lambda_handler",
            role=role,
            timeout=Duration.seconds(180),
            memory_size=512,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            vpc=vpc
        )
        
        # Defines an Amazon API Gateway endpoint for Image Generation service
        txt2img_apigw_endpoint = apigw.LambdaRestApi(
            self, "txt2img_apigw_endpoint",
            handler=lambda_txt2img
        )
        
        # Defines an AWS Lambda function for NLU & Text Generation service
        lambda_txt2nlu = _lambda.Function(
            self, "lambda_txt2nlu",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("code/lambda_txt2nlu"),
            handler="txt2nlu.lambda_handler",
            role=role,
            timeout=Duration.seconds(180),
            memory_size=512,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            vpc=vpc            
        )
        
        # Defines an Amazon API Gateway endpoint for NLU & Text Generation service
        txt2nlu_apigw_endpoint = apigw.LambdaRestApi(
            self, "txt2nlu_apigw_endpoint",
            handler=lambda_txt2nlu
        )        
        
        # Create ECS cluster
        cluster = ecs.Cluster(self, "WebDemoCluster", vpc=vpc)

        # Create an IAM role for the EC2 instances
        instance_role = iam.Role(
            self, "EcsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore") # Optional: for SSM agent
            ]
        )

        # Create a launch template
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            f"echo ECS_CLUSTER={cluster.cluster_name} >> /etc/ecs/ecs.config",
            "sudo iptables --insert FORWARD 1 --in-interface docker+ --destination 169.254.169.254/32 --jump DROP",
            "sudo service iptables save",
            "echo ECS_AWSVPC_BLOCK_IMDS=true >> /etc/ecs/ecs.config"
        )
        
        # Create the launch template
        launch_template = ec2.LaunchTemplate(
            self, "EcsSpotLaunchTemplate",
            launch_template_name="EcsSpotLaunchTemplate",
            instance_type=ec2.InstanceType("c5.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            user_data=user_data,
            role=instance_role, # Assign the role to the launch template
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(30) # Increased from 20 to 30 GB to match the snapshot size requirements
                )
            ],
            # Add Spot options with ONE_TIME request type (required for AutoScaling)
            spot_options=ec2.LaunchTemplateSpotOptions(
                max_price=0.0735, # Set max price for Spot Instances
                request_type=ec2.SpotRequestType.ONE_TIME # Changed from PERSISTENT to ONE_TIME as required by AutoScaling
            )
        )
        
        # Create the Auto Scaling Group with the launch template
        asg = autoscaling.AutoScalingGroup(
            self, "AsgSpotNew",  # Changed ID to ensure a new resource is created
            vpc=vpc,
            min_capacity=1,
            max_capacity=2,
            #desired_capacity=2,
            launch_template=launch_template,  # Use the launch template instead of instance properties
        )
        
        # Add the ASG capacity to the ECS cluster
        capacity_provider = ecs.AsgCapacityProvider(
            self, "AsgCapacityProvider",
            auto_scaling_group=asg,
            enable_managed_termination_protection=False,
            spot_instance_draining=True
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        # Build Dockerfile from local folder and push to ECR
        image = ecs.ContainerImage.from_asset("web-app")

        # Create Fargate service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "WebApplication",
            cluster=cluster,            # Required
            cpu=2048,                   # Default is 256 (512 is 0.5 vCPU, 2048 is 2 vCPU)
            desired_count=1,            # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image, 
                container_port=8501,
                ),
            #load_balancer_name="gen-ai-demo",
            memory_limit_mib=4096,      # Default is 512
            public_load_balancer=True)  # Default is True


        fargate_service.task_definition.add_to_task_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions = ["ssm:GetParameter"],
            resources = ["arn:aws:ssm:*"],
            )
        )  
        
        fargate_service.task_definition.add_to_task_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions = ["execute-api:Invoke","execute-api:ManageConnections"],
            resources = ["*"],
            )
        )          


        # Setup task auto-scaling
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=10
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        ssm.StringParameter(self, "txt2img_api_endpoint", parameter_name="txt2img_api_endpoint", string_value=txt2img_apigw_endpoint.url)
        ssm.StringParameter(self, "txt2nlu_api_endpoint", parameter_name="txt2nlu_api_endpoint", string_value=txt2nlu_apigw_endpoint.url)