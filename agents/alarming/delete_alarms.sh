#!/bin/bash
aws cloudwatch describe-alarms --query 'MetricAlarms[].AlarmName' --output text | xargs -r aws cloudwatch delete-alarms --alarm-names