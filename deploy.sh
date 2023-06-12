#!/usr/bin/bash

if [ "$#" != "1" ]; then
    echo "Usage: deploy <version-number>"
    exit 1
fi

BUCKET="edu.au.cs.image-gallery-config"

aws s3 cp ec2-scripts/ec2-prod-$1.sh s3://${BUCKET}
aws s3 sync nginx s3://${BUCKET}/nginx

