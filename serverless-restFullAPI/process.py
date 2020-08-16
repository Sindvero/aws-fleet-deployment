import boto3
import time

parameters = {
        'num_nodes': 0,
        'subnets': '',
        'security_groups': '',
        'iam_fleet_role': '',
        'instances_types': '',
        'multi_attach_vol_size': 0,
        'ami_id': ''
    }

def deployFleet():
    SPOTRATE = 0.8 # 80% on spot
    ONDEMANDRATE = 1/5 # 20% on-demand
    ec2 = boto3.client('ec2')

    targetWanted = parameters['num_nodes']
    spotCapacity = int(targetWanted * SPOTRATE)
    demandCapacity = int(targetWanted * ONDEMANDRATE)
    availableInstances = 0 #available = True if state=running and io1 ebs volume attached
    instanceIds = []
    volumeId = ''
    subnets = parameters['subnets']
    subnetsList = subnets.split(',')
    securityGroup = parameters['security_groups']
    iamFleetRole = parameters['iam_fleet_role']
    instanceType = parameters['instances_types']
    sizeAttached = parameters['multi_attach_vol_size']
    imageId = parameters['ami_id']
    
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
    
    
    
def lambda_handler(event, context):
    global parameters
    num_nodes = int(event['num_nodes'])
    subnets = event['subnets']
    security_groups = event['security_groups']
    iam_fleet_role = event['iam_fleet_role']
    instances_types = event['instances_types']
    multi_attach_vol_size = int(event['multi_attach_vol_size'])
    ami_id = event['ami_id']
    if not instances_types:
        instances_types = 't3.micro'
    if not multi_attach_vol_size:
        multi_attach_vol_size = 3
    if not ami_id:
        ami_id = 'ami-0ac80df6eff0e70b5'
    
    parameters['num_nodes'] = num_nodes
    parameters['subnets'] = subnets
    parameters['security_groups'] = security_groups
    parameters['iam_fleet_role'] = iam_fleet_role
    parameters['instances_types'] = instances_types
    parameters['multi_attach_vol_size'] = multi_attach_vol_size
    parameters['ami_id'] = ami_id
    
    deployFleet()
    return parameters
