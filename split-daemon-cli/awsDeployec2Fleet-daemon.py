import os
import sys
import atexit
import boto3
import time

thefifo = 'comms.fifo'
os.mkfifo(thefifo)
parameters = []
# Clean when kill
def cleanup():
    os.remove(thefifo)
atexit.register(cleanup)

def getParameters(parameter):
    global parameters
    parameters.append(parameter)


def deployment():
    ec2 = boto3.client('ec2')
    SPOTRATE = 0.8 # 80% on spot
    ONDEMANDRATE = 1/5 # 20% on-demand
    targetWanted = int(parameters[0])
    spotCapacity = int(targetWanted * SPOTRATE)
    demandCapacity = int(targetWanted * ONDEMANDRATE)
    availableInstances = 0 #available = True if state=running and io1 ebs volume attached
    instanceIds = []
    volumeId = ''
    subnets = parameters[1]
    subnetsList = subnets.split(',')
    securityGroup = parameters[2]
    iamFleetRole = parameters[3]
    instanceType = parameters[4]
    sizeAttached = parameters[5]
    imageId = parameters[6]
    
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
    time.sleep(20)
    def attachVolume(AZ, instanceId):
        global volumeId
        global availableInstances
        global attachedVolumeinAZ
        global sizeAttached

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
    

while True:
    with open(thefifo, 'r') as fifo:
        for line in fifo:
            getParameters(line.strip())
    deployment()
    parameters.clear()
