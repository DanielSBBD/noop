import json
import boto3

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event, indent=2)}")

    for record in event['Records']:
        sns_message = record['Sns']['Message']
        alarm_data = json.loads(sns_message)
    
        # Extract comprehensive alarm details from CloudWatch alarm event
        alarm_name = alarm_data['AlarmName']
        alarm_description = alarm_data.get('AlarmDescription', '')
        new_state = alarm_data['NewStateValue']
        old_state = alarm_data.get('OldStateValue', 'Unknown')
        reason = alarm_data['NewStateReason']
        region = alarm_data['Region']
        account_id = alarm_data['AWSAccountId']
        
        # Extract metric details if available
        metric_name = alarm_data.get('MetricName', 'Unknown')
        namespace = alarm_data.get('Namespace', 'Unknown')
        dimensions = alarm_data.get('Dimensions', {})
    
        prompt = f"""
Investigate this alarm to find the root cause.

Name: {alarm_name}
Description: {alarm_description}
State: {old_state} → {new_state}
Reason: {reason}
Timestamp: {event['StateChangeTime']}
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
            
            