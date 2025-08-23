import json
import boto3

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event, indent=2)}")

    # Extract alarm details from direct CloudWatch alarm event
    alarm_name = event['alarmData']['alarmName']
    alarm_description = event['alarmData']['configuration'].get('description', '')
    new_state = event['alarmData']['state']['value']
    old_state = event['alarmData']['previousState']['value']
    reason = event['alarmData']['state']['reason']
    region = event['region']
    account_id = event['accountId']
    
    # Extract metric details
    metric_config = event['alarmData']['configuration']['metrics'][0]['metricStat']['metric']
    metric_name = metric_config['name']
    namespace = metric_config['namespace']
    dimensions = metric_config.get('dimensions', {})

    prompt = f"""
Investigate this alarm to find the root cause.

Name: {alarm_name}
Description: {alarm_description}
State: {old_state} → {new_state}
Reason: {reason}
Timestamp: {event['time']}
Region: {region}
Account: {account_id}
Metric: {namespace}/{metric_name}
Dimensions: {json.dumps(dimensions, indent=2)}
    """.strip()

    bedrock_client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    sns_client = boto3.client('sns', region_name='us-east-1')
    
    try:
        response = bedrock_client.invoke_agent_runtime(
            agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:129463259399:runtime/investigator-JB4TCCB1ao",
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": prompt}).encode(),
        )

        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        
        result = json.loads(''.join(content))
        
        # Send investigation results to SNS
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:129463259399:AlarmInvestigations',
            Subject=f'Alarm Investigation: {alarm_name}',
            Message=json.dumps({
                'alarm': alarm_name,
                'investigation': result
            }, indent=2)
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
    return {
        'statusCode': 200,
        'body': 'success'
    }
            
            