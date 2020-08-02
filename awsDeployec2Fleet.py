#!/usr/bin/env python

import boto3
import sys
import time

# It's not the perfect script, I know that I could make some improvment such as using the aws waiter, using a class,... 
# However, it works well and I think I check all the required boxes :)
ec2 = boto3.client('ec2')

if (len(sys.argv) < 2):
    print("Usage: " + sys.argv[0] + " <Options>")
    print("\t")
    print("Options = <destroy>: To destroy your entire environment")
    print("          <NumberofInstance desired (int)> <Security group ID (str)>")
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
if (len(sys.argv) < 3):
    print("Usage: " + sys.argv[0] + " <Options>")
    print("\t")
    print("Options = <NumberofInstance desired (int)> <Security group ID (str)")
    sys.exit(1)

targetWanted = sys.argv[1]
availableInstances = 0 #available = True if state=running and io1 ebs volume attached
instanceIds = []
volumeId = ''
securityGroup = sys.argv[2]
attachedVolumeinAZ = {'us-east-1f': 0, 'us-east-1c': 0} #Add other AZs here that you may want
fleet = ec2.request_spot_fleet(
            SpotFleetRequestConfig={
                'TargetCapacity': targetWanted,
                'IamFleetRole': 'arn:aws:iam::964862435125:role/aws-ec2-spot-fleet-tagging-role',#It's a default one, you can change it if you want to.
                'LaunchSpecifications': [
                    {
                        'ImageId': 'ami-0ac80df6eff0e70b5',#If you want to change the image, you need to change this ID
                        # 'KeyName': 'YourKeyName',
                        'SecurityGroups': [
                            {
                                'GroupId': securityGroup #Please change to your security gr
                            }
                        ],
                        'InstanceType': 't3.large',
                        'Placement': {
                            'AvailabilityZone': 'us-east-1f, us-east-1c'#If you want to add more AZ
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
    if (attachedVolumeinAZ[AZ] > 16 or availableInstances == 0):
        newVolume = ec2.create_volume(
            AvailabilityZone=AZ,
            Iops=150,
            Size=8,
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
