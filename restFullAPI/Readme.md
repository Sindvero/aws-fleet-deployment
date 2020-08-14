# Automate to deploy AWS' EC2 fleet running on spot instances

## restFull API using flask

To use this Python script, please make sure to have the last boto3 version install (v1.14.32) and to install flask:
```
pip3 install boto3
```
or 
```
pip3 install boto3==1.14.32
```

```
pip3 install flask
```

If you want to create your environment:
```
python3 awsDeployec2Fleet-server.py 
chmod +x client.sh
./client.sh <num_nodes> <subnets (min=2)> <security_groups (min=1)> <iam_fleet_role> [instances_types] [multi_attach_vol_size] [ami_id]
```