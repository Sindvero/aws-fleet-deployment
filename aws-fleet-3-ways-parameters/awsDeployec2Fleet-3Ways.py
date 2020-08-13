import os
import sys
import boto3
import time
import json

argc = len(sys.argv)
SPOTRATE = 0.8 # 80% on spot
ONDEMANDRATE = 1/5 # 20% on-demand
ec2 = boto3.client('ec2')
targetWanted = 0
securityGroup = ''
iamFleetRole = ''
subnets = ''
subnetsList = []
instanceType = 't3.micro'
imageId = 'ami-0ac80df6eff0e70b5'
sizeAttached = 3


if (argc == 1):
    if 'NUM_NODES' in os.environ:
        targetWanted = int(os.environ['NUM_NODES'])
        spotCapacity = int(targetWanted * SPOTRATE)
        demandCapacity = int(targetWanted * ONDEMANDRATE)
    else:
        print("Please set your environment variable 'NUM_NODES' to the desired numbers of nodes.")
        sys.exit(1)
    
    if 'SUBNETS' in os.environ:
        subnets = os.environ['SUBNETS']
        subnetsList = subnets.split(',')
        if (len(subnetsList < 2)):
            print("Please give at least 2 subnets ID")
            sys.exit(1)
    else:
        print("Please set your environment variable 'SUBNETS' to the desired subnets (min=2).")
        sys,exit(1)
    
    if 'SECURITY_GROUPS' in os.environ:
        securityGroup = os.environ['SECURITY_GROUPS']
    else:
        print("Please set your environment variable 'SECURITY_GROUPS' to the desired security groups (min=1).")
        sys.exit(1)
    
    if 'IAM_FLEET_ROLE' in os.environ:
        iamFleetRole = os.environ['IAM_FLEET_ROLE']
    else:
        print("Please set your environment variable 'IAM_FLEET_ROLE' to the desired IAM fleet role.")
        sys.exit(1)

    if 'INSTANCES_TYPE' in os.environ:
        instanceType = os.environ['INSTANCES_TYPE']
    
    if 'MULTI_ATTACH_VOL_SIZE' in os.environ:
        sizeAttached = os.environ['MULTI_ATTACH_VOL_SIZE']
    
    if 'AMI_ID' in os.environ:
        imageId = os.environ['AMI_ID']

elif (argc == 2):
    if ('json' in sys.argv[1]): # For json, I consider that the user has respected the usage and type of the paraneters
        with open(sys.argv[1]) as jsonFile:
            parameters = json.load(jsonFile)
        targetWanted = parameters['num_nodes']
        spotCapacity = int(targetWanted * SPOTRATE)
        demandCapacity = int(targetWanted * ONDEMANDRATE)
        subnetsList = parameters['subnets']
        if (len(subnetsList) < 2):
            print("Please Provide at least 2 subnets ID")
            sys.exit(1)
        subnets = ",".join(subnetsList)
        securityGroup = parameters['security_groups']
        iamFleetRole = parameters['iam_fleet_role']

        if 'instances_types' in parameters:
            instanceType = parameters['instances_types']
        if 'multi_attach_vol_size' in parameters:
            sizeAttached = parameters['multi_attach_vol_size']
        if 'ami_id' in parameters:
            imageId = parameters['ami_id']


    else:
        print("Usage: " + sys.argv[0] + " <Options>")
        print("\t")
        print("Options = <num_nodes (int)> <subnets (arr, min=2)> <security_groups (arr, min=1)> <iam_fleet_role (str)> [instances_types (str)] [multi_attach_vol_size (int)] [ami_id (str)]")
        sys.exit(1)

elif (argc > 2 and argc < 5):
    print("Usage: " + sys.argv[0] + " <Options>")
    print("\t")
    print("Options = <num_nodes (int)> <subnets (arr, min=2)> <security_groups (arr, min=1)> <iam_fleet_role (str)> [instances_types (str)] [multi_attach_vol_size (int)] [ami_id (str)]")
    sys.exit(1)

else:
    targetWanted = int(sys.argv[1])
    spotCapacity = int(targetWanted * SPOTRATE)
    demandCapacity = int(targetWanted * ONDEMANDRATE)
    securityGroup = sys.argv[3]
    iamFleetRole = sys.argv[4]
    subnets = sys.argv[2]
    subnetsList = subnets.split(',')
    if (len(subnetsList < 2)):
        print("Please give at least 2 subnets ID")
        sys.exit(1)

    if (argc >= 6):
        instanceType = sys.argv[5]
    if (argc >= 8):
        imageId = sys.argv[7]
    if (argc >= 7):
        sizeAttached = int(sys.argv[6])

availableInstances = 0 #available = True if state=running and io1 ebs volume attached
instanceIds = []
volumeId = ''
attachedVolumeinAZ = {} 
for subnet in subnetsList:
    attachedVolumeinAZ[subnet] = 0

fleet = ec2.request_spot_fleet(
            SpotFleetRequestConfig={
                'TargetCapacity': spotCapacity,
                'OnDemandTargetCapacity': demandCapacity,
                'IamFleetRole': iamFleetRole, #Make sure you have the config to deploy spot fleet
                'LaunchSpecifications': [
                    {
                        'ImageId': imageId,
                        # 'KeyName': 'YourKeyName',
                        'SecurityGroups': [
                            {
                                'GroupId': securityGroup
                            }
                        ],
                        'InstanceType': instanceType,
                        'Placement': {
                            'AvailabilityZone': subnets 
                        }
                    }
                ],
                'AllocationStrategy': 'lowestPrice'
            }
        )
time.sleep(20) #Better practice: use the waiter from the SDK.

def attachVolume(AZ, instanceId):
    global volumeId
    global availableInstances
    global attachedVolumeinAZ
    global sizeAttached
    if (argc >= 7):
        sizeAttached = int(sys.argv[6])

    if (attachedVolumeinAZ[AZ] > 16 or availableInstances == 0 or attachedVolumeinAZ[AZ] == 0):
        newVolume = ec2.create_volume(
            AvailabilityZone=AZ,
            Iops=150,
            Size=sizeAttached,
            VolumeType='io1',
            MultiAttachEnabled=True
        )
        volumeId = newVolume['VolumeId']
        attachedVolumeinAZ[AZ] = 0
        time.sleep(5)

    ec2.attach_volume(
        Device='/dev/sda2',
        InstanceId=instanceId,
        VolumeId=volumeId
    )
    availableInstances = availableInstances + 1
    print("New instance online (Id = " + instanceId + "). Total = " + str(availableInstances))

while(availableInstances != targetWanted):
    availableInstancesParameter = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': [
                        'running'
                    ]
                }
            ]
        )
    
    for r in availableInstancesParameter['Reservations']:
        for i in r['Instances']:
            if (i['InstanceId'] not in instanceIds):
                instanceIds.append({'instanceId': i['InstanceId'], 'AZ': i['Placement']['AvailabilityZone']}) #Get the instances IDs (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances)
    
    instanceId = instanceIds[availableInstances]['instanceId']
    AZ = instanceIds[availableInstances]['AZ']

    attachVolume(AZ, instanceId)
    attachedVolumeinAZ[AZ] = attachedVolumeinAZ[AZ] + 1
