#!/bin/sh

argc=$#

if [ $argc -lt 4 ]; then
    echo "Client for EC2 fleet deployment\n"
    echo
    echo "Syntax: $0 <num_nodes> <subnets (min=2)> <security_groups (min=1)> <iam_fleet_role> [instances_types] [multi_attach_vol_size] [ami_id]\n"
    echo
    exit 1
fi

targetWanted=$1
subnets=$2
securityGroups=$3
iamFleetRole=$4
instanceType=$5
size=$6
imageId=$7

request=$targetWanted'&'$subnets'&'$securityGroups'&'$iamFleetRole
if [ $argc -ge 5 ]; then
    request=$targetWanted'&'$subnets'&'$securityGroups'&'$iamFleetRole'&'$instanceType
fi

if [ $argc -ge 6 ]; then
    request=$targetWanted'&'$subnets'&'$securityGroups'&'$iamFleetRole'&'$instanceType'&'$size
fi

if [ $argc -ge 7 ]; then
    request=$targetWanted'&'$subnets'&'$securityGroups'&'$iamFleetRole'&'$instanceType'&'$size'&'$imageId
fi

curl -X POST http://localhost:5000/"$request"/