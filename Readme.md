# Automate to deploy AWS' EC2 fleet running on spot instances

To use this Python script, please make sure to have the last boto3 version install (v1.14.32):
```
pip3 (or pip) install boto3
```
or 
```
pip3 (or pip) install boto3==1.14.32
```

If you want to destroy your environment:
```
python3 awsDeployec2Fleet.py destroy
```

If you want to create your environment:
```
python3 awsDeployec2Fleet.py <num_nodes (int)> <subnets (arr, min=2)> <security_groups (arr, min=1)> <iam_fleet_role (str)> [instances_types (str)] [multi_attach_vol_size (int)] [ami_id (str)]
```

The fleet deployed will span across 2 AZs (If you want to add another AZ, please add it by following the comments in the code)