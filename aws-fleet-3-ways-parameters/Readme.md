# Automate to deploy AWS' EC2 fleet running on spot instances

## 3 ways of receiving parameters

To use this Python script, please make sure to have the last boto3 version install (v1.14.32):
```
pip3 (or pip) install boto3
```
or 
```
pip3 (or pip) install boto3==1.14.32
```

You have 3 choices to create your instances:

-   Set your environment variables:
```
export NUM_NODES=3
export SUBNETS=us-east-1f,us-east-1c
export SECURITY_GROUPS=mySecurityGr
export IAM_FLEET_ROLE=myIAMFleetRole
```
these are optionals:
```
export INSTANCES_TYPE=desiredInstanceType
export MULTI_ATTACH_VOL_SIZE=desiredSize (in GB)
export AMI_ID=desiredImageId
```

-   Give a Json file as input:

```
python3 awsDeployec2Fleet.py myConfig.json
```

- Command line input:
```
python3 awsDeployec2Fleet.py <num_nodes> <subnets (min=2)> <security_groups (min=1)> <iam_fleet_role> [instances_types] [multi_attach_vol_size] [ami_id]
```

The fleet deployed will span across at least 2 AZs.