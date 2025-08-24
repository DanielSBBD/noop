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

Ensure that you ONLY output HTML in your response to be sent as an email to the client. Keep the emal concise but make it look pretty with sections and tables where necessary. Use - Use '#6d28d9' for the main colour theme
    """.strip()

    from botocore.config import Config
    config = Config(read_timeout=900)  # 15 minutes
    bedrock_client = boto3.client('bedrock-agentcore', region_name='us-east-1', config=config)
    ses_client = boto3.client('ses', region_name='us-east-1')
    logs_client = boto3.client('logs', region_name='us-east-1')
    
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
        print(f"Agent result structure: {result}")
        
        # Handle different possible response structures
        if 'content' in result:
            agent_response = result['content'][0]['text'].strip()
        elif 'response' in result:
            agent_response = result['response']
        else:
            agent_response = str(result)
        
        print(f"Agent response: {agent_response}")
        
        # Extract HTML content more safely
        if '<html>' in agent_response and '</html>' in agent_response:
            html = agent_response.split('<html>')[1].split('</html>')[0]
        else:
            # If no HTML tags, wrap the response in basic HTML
            html = f"<h2>Alarm Investigation: {alarm_name}</h2><p>{agent_response}</p>"
        
        # Clean up HTML content - remove literal \n characters and extra whitespace
        html = html.replace('\n', '').replace('\\n', '').strip()
        
        print(f"HTML content: {html}")

        # Log investigation to CloudWatch Logs
        import time
        log_stream_name = f"{alarm_name}-{int(time.time())}"
        
        try:
            logs_client.create_log_stream(
                logGroupName='noop/alarm-investigations',
                logStreamName=log_stream_name
            )
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        log_message = {
            "timestamp": event['time'],
            "alarm_name": alarm_name,
            "state_change": f"{old_state} → {new_state}",
            "reason": reason,
            "investigation": agent_response
        }
        
        logs_client.put_log_events(
            logGroupName='noop/alarm-investigations',
            logStreamName=log_stream_name,
            logEvents=[
                {
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(log_message, indent=2)
                }
            ]
        )

        response = ses_client.send_email(
            Source="alarms@bbd-mserv.com",
            Destination={
                'ToAddresses': ["michael.rolle@bbd.co.za", "daniels@bbd.co.za", "wernerd@bbd.co.za"]
            },
            Message={
                'Subject': {
                    'Data': f'Alarm Investigation: {alarm_name}'
                },
                'Body': {
                    'Html': {
                        'Data': html
                    }
                }
            },
        )
    except Exception as e:
        print(f"Error details: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
    return {
        'statusCode': 200,
        'body': 'success'
    }
            
            