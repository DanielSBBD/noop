import json
import boto3
from typing import Dict, Any
from datetime import datetime
import logging

from strands.agent.agent import Agent
from strands.tools.decorator import tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

def is_read_operation(operation: str) -> bool:
  """Check if an AWS API operation is read-only."""
  read_prefixes = [
      'describe', 'list', 'get', 'fetch', 'read', 'query', 'search', 
      'lookup', 'find', 'check', 'validate', 'inspect', 'scan',
      'head', 'exists', 'count', 'estimate', 'preview', 'show', 'filter'
  ]
  return any(operation.lower().startswith(prefix) for prefix in read_prefixes)

def json_serializer(obj):
  if isinstance(obj, datetime):
      return obj.isoformat()
  raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@tool
def invoke_aws_api(service: str, operation: str, parameters: str = "{}") -> Dict[str, Any]:
    """
    Invoke AWS API operations dynamically. Only allows read-only operations.
    
    Args:
        service (str): The boto3 AWS service name (e.g., 'ec2', 'logs', 'cloudwatch')
        operation (str): The boto3 AWS service API operation name (e.g., 'describe_instances', 'describe_log_groups')
        parameters (str): JSON string of boto3 parameters for the API call
        
    Returns:
        Dict[str, Any]: The API response
    """
    try:
        # Parse parameters
        try:
            api_parameters = json.loads(parameters)
            if api_parameters is None:
                api_parameters = {}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in parameters: {str(e)}"}

        # Validate operation is read-only
        if not is_read_operation(operation):
            return {"error": f"Operation '{operation}' is not allowed. Only read operations are permitted."}

        # Create AWS client and invoke operation
        if not service:
            return {"error": "Service name must be specified for invoking AWS API operations."}
        if not operation:
            return {"error": "Operation name must be specified for invoking AWS API operations."}
        client = boto3.client(service)
        method = getattr(client, operation, None)
        
        if not method:
            return {"error": f"Operation '{operation}' not found in service '{service}'"}

        response = method(**api_parameters)
        
        try:
            serialized_response = json.loads(json.dumps(response, default=json_serializer))
        except Exception:
            serialized_response = str(response)

        return {
            'function': 'invoke_aws_api',
            'service': service,
            'operation': operation,
            'response': serialized_response
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def list_resources() -> Dict[str, Any]:
    """
    List all resources in the account.
    
    Returns:
        Dict[str, Any]: List of resources
    """
    try:
        client = boto3.client('resourcegroupstaggingapi')
        resources = client.get_resources()
        return {
            'function': 'list_resources',
            'resources': resources
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def list_available_services() -> Dict[str, Any]:
    """
    List all available boto3 AWS services.
    
    Returns:
        Dict[str, Any]: List of available AWS services
    """
    try:
        session = boto3.Session()
        available_services = session.get_available_services()

        return {
            'function': 'list_available_services',
            'services': available_services
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def list_service_operations(service: str) -> Dict[str, Any]:
    """
    List all read-only operations for a given boto3 AWS service.
    
    Args:
        service (str): The boto3 AWS service name
        
    Returns:
        Dict[str, Any]: List of available operations
    """
    try:
        session = boto3.Session()
        client = session.client(service)
        operations = [method for method in dir(client) 
                     if callable(getattr(client, method)) and not method.startswith('_')]
        read_operations = [op for op in operations if is_read_operation(op)]
        
        return {
            'function': 'list_service_operations',
            'service': service,
            'operations': read_operations,
            'total_operations': len(read_operations)
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def read_account_discovery_results() -> Dict[str, Any]:
    """
    Read information about the resources in the account.
    
    Returns:
        Dict[str, Any]: Account discovery results
    """
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(
            Bucket='noop-storage',
            Key='discovery-results.md'
        )
        return {
            'function': 'read_account_discovery_results',
            'results': response['Body'].read().decode('utf-8')
        }
    except Exception as e:
        return {"error": str(e)}


# Create a BedrockModel with the same configuration as in agent.tf
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-east-1"
)

# MSP Support Agent Instructions
msp_agent_instructions = """
You are an expert AWS support engineer. Your task is to answer any questions the user asks you using the information sources provided to you.

**Core Principles**
- Make as few AWS API calls as possible to answer the user's question properly.
- Provide your answer in the form of a markdown document. Make sure to keep your answer concise and to the point.
- If there is any additional information you need from the user to generate a proper report, ask the user for the information, do not make assumptions.
- Provide a list of the tools you used to answer the user's question.
- If you aren't able to fetch the information the user is asking for, say so.
- If you are asked to answer questions about the alarm investigations, read from the `noop/alarm-investigations` log group.

**Guidelines**
You have been provided with a set of tools to answer the user's question. You will ALWAYS follow the below guidelines when you are answering a question:
- Think through the user's question, extract all data from the question before creating a plan.
"""

# Initialize Bedrock Agent Core App
app = BedrockAgentCoreApp()
agent = Agent(
    model=bedrock_model, 
    system_prompt=msp_agent_instructions,
    tools=[invoke_aws_api, list_available_services, list_service_operations, list_resources, read_account_discovery_results]
)

@app.entrypoint
def invoke(payload):
    """
    Process user input and return a response for MSP support scenarios.
    
    Args:
        payload (dict): The input payload containing the prompt and any additional data
        
    Returns:
        dict: The agent's response with investigation results
    """
    try:
        # Extract the user message from the payload
        user_message = payload.get("prompt", "No prompt found in input. Please provide alert information for investigation.")
        
        # Log the incoming request
        logging.info(f"Received request with prompt: {user_message[:200]}...")
        
        response = agent(user_message)

        return {"response": response.message}
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logging.error(error_msg)
        return {"message": error_msg}

# Health check endpoint is automatically handled by BedrockAgentCoreApp
if __name__ == "__main__":
    logging.info("Starting MSP Support Agent for Bedrock Agent Core...")
    app.run()
