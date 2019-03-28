#!/usr/bin/env bash
export AWS_ACCESS_KEY_ID=$(aws --profile sandbox configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws --profile sandbox configure get aws_secret_access_key)

sudo docker run -d -p 5000:5000 --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY simple-serverless-rule-engine:latest