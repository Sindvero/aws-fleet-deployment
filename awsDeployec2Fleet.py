#!/usr/bin/env python

import boto3
import sys
import time

SPOTRATE = 0.8 # 80% on spot
ONDEMANDRATE = 1/5 # 20% on-demand
argc = len(sys.argv)
ec2 = boto3.client('ec2')

if (len(sys.argv) < 2):
    print("Usage: " + sys.argv[0] + " <Options>")
    print("\t")
    print("Options = <destroy>: To destroy your entire environment")
    print("          <num_nodes (int)> <subnets (arr, min=2)> <security_groups (arr, min=1)> <iam_fleet_role (str)> [instances_types (str)] [multi_attach_vol_size (int)] [ami_id (str)]")
    sys.exit(1)

###############################
#       Destroy environment
###############################
if (sys.argv[1] == "destroy"):
    fleetId = ec2.describe_spot_fleet_requests(MaxResults=1)['SpotFleetRequestConfigs'][0]['SpotFleetRequestId']
    destroyFleet = ec2.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[
            fleetId
        ],
        TerminateInstances=True
    )
    print(destroyFleet)
    sys.exit(0)


###############################
#       Create environment
###############################
if (argc < 5):
    print("Usage: " + sys.argv[0] + " <Options>")
    print("\t")
    print("Options = <num_nodes (int)> <subnets (arr, min=2)> <security_groups (arr, min=1)> <iam_fleet_role (str)> [instances_types (str)] [multi_attach_vol_size (int)] [ami_id (str)]")
    sys.exit(1)

targetWanted = int(sys.argv[1])
spotCapacity = int(targetWanted * SPOTRATE)
demandCapacity = int(targetWanted * ONDEMANDRATE)
availableInstances = 0 #available = True if state=running and io1 ebs volume attached
instanceIds = []
volumeId = ''
securityGroup = sys.argv[3]
iamFleetRole = sys.argv[4]
subnets = sys.argv[2]
subnetsList = subnets.split(',')
if (len(subnetsList < 2)):
    print("Please give at least 2 subnets ID")
    sys.exit(1)
    
attachedVolumeinAZ = {} 
for subnet in subnetsList:
    attachedVolumeinAZ[subnet] = 0

instanceType = 't3.micro'
if (argc >= 6):
    instanceType = sys.argv[5]

imageId = 'ami-0ac80df6eff0e70b5'
if (argc >= 8):
    imageId = sys.argv[7]

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
    sizeAttached = 3
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
