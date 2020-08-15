# Automate to deploy AWS' EC2 fleet running on spot instances

## serverless restFul API using Lambda function and APIGateway

First and foremost you nees to create your lambda function with the process.py script I created:
```
zip zip lambda-process.zip process.py
aws lambda create-function --function-name lambda-function-aws-ec2-fleet --runtime python3.6 --zip-file fileb://lambda-process.zip --timeout 800 --handler process.lambda_handler --role <Your-arn-role>
```

Then you need to create your APIGateway (Unfortunately, I can't automate this because AWS cli and AWS SDK don't seem to have the features to configure correctly the RestAPI):

-   Go to https://console.aws.amazon.com/apigateway/
-   Click on "Create API" -> under REST API, click on "Build"
-   Under "Create new API", check "New API", Choose your api's name and click "Create API"
-   Click on "Action" -> "Create Method" -> Choose "POST"
-   In the Setup, check "Lambda Function", choose the region where your lambda is located, provide lambda-function-aws-ec2-fleet under lambda name
-   Click on "Method Request" -> "URL Query String Parameters" -> "Add query string" and enter the following string (1 query string at the time):
    -   num_nodes
    -   subnets
    -   security_groups
    -   iam_fleet_role
    -   instances_types
    -   multi_attach_vol_size
    -   ami_id
-   Go back -> click on "Integration Request" -> "Mapping Templates" -> check "When there are no templates defined (recommended)" -> "Add mapping template" -> under "Content-Type", write "application/json"
-   In the JSON window at the bottom paste this:
    ```
    {
    "num_nodes": "$input.params('num_nodes')",
    "subnets": "$input.params('subnets')",
    "security_groups": "$input.params('security_groups')",
    "iam_fleet_role": "$input.params('iam_fleet_role')",
    "instances_types": "$input.params('instances_types')",
    "multi_attach_vol_size": "$input.params('multi_attach_vol_size')",
    "ami_id": "$input.params('ami_id')"
    }
    ```
-   Save, Go back, click on "Action" -> "Deploy API" -> "OK"
-   In stage, get the "Invoke URL", you will need it to deploy your EC2 fleet.

Then, to create your environment:
```
chmod +x client.sh
./client.sh <num_nodes> <subnets (min=2)> <security_groups (min=1)> <iam_fleet_role> [instances_types] [multi_attach_vol_size] [ami_id] <Your Invoke URL>
```

[options] = Optionnal
\<options\> = Mandatory
