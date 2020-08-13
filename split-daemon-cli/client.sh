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
instanceType='t3.micro'
if [ $argc -ge 5 ]; then
    instanceType=$5
fi

imageId='ami-0ac80df6eff0e70b5'
if [ $argc -ge 6 ]; then
    imageId=$6
fi

size=3
if [ $argc -ge 7 ]; then
    size=$7
fi

echo $targetWanted >> comms.fifo;
echo $subnets >> comms.fifo;
echo $securityGroups >> comms.fifo;
echo $iamFleetRole >> comms.fifo;
echo $instanceType >> comms.fifo;
echo $imageId >> comms.fifo;
echo $size >> comms.fifo
