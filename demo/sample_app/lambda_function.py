import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set Failure Mode
FAILURE_MODE = "none" # none, external_api_failure

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Demo Lambda function that serves a simple web page.
    This function is designed to work or fail for testing purposes.
    """
    try:
        # Log the incoming request
        logger.info(f"Received request: {json.dumps(event)}")
        
        # Get the HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Log request details
        logger.info(f"Processing {http_method} request to {path}")
        
        if FAILURE_MODE == 'external_api_failure':
            # Simulate external API dependency failure
            logger.info("Calling external payment validation API...")
            time.sleep(1)  # Simulate API call
            logger.error("External API returned HTTP 503 Service Unavailable")
            raise Exception("Payment validation service unavailable: https://api.payments.example.com returned 503")
        
        # Generate a realistic web service response
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CloudTech Solutions - API Gateway</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem 0; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 0 2rem; }}
                .nav {{ display: flex; justify-content: space-between; align-items: center; }}
                .logo {{ font-size: 1.5rem; font-weight: bold; }}
                .main {{ padding: 3rem 0; }}
                .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 2rem; margin-bottom: 2rem; }}
                .status-badge {{ display: inline-block; background: #10b981; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem; }}
                .metric {{ background: #f8fafc; padding: 1rem; border-radius: 6px; text-align: center; }}
                .metric-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
                .metric-label {{ color: #64748b; font-size: 0.9rem; }}
                .footer {{ background: #1e293b; color: #94a3b8; text-align: center; padding: 2rem 0; }}
            </style>
        </head>
        <body>
            <header class="header">
                <div class="container">
                    <nav class="nav">
                        <div class="logo">CloudTech Solutions</div>
                        <div>API Gateway v2.1.4</div>
                    </nav>
                </div>
            </header>
            
            <main class="main">
                <div class="container">
                    <div class="card">
                        <h1>Service Health Dashboard</h1>
                        <p><span class="status-badge">✓ All Systems Operational</span></p>
                        
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-value">99.9%</div>
                                <div class="metric-label">Uptime</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">45ms</div>
                                <div class="metric-label">Avg Response</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">1.2K</div>
                                <div class="metric-label">Requests/min</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">8</div>
                                <div class="metric-label">Active Services</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>Request Details</h2>
                        <p><strong>Timestamp:</strong> {current_time}</p>
                        <p><strong>Request ID:</strong> {context.aws_request_id if context else 'req_' + str(int(time.time()))}</p>
                        <p><strong>Region:</strong> us-east-1</p>
                        <p><strong>Environment:</strong> Production</p>
                    </div>
                </div>
            </main>
            
            <footer class="footer">
                <div class="container">
                    <p>&copy; 2024 CloudTech Solutions. All rights reserved. | Support: support@cloudtech.com</p>
                </div>
            </footer>
        </body>
        </html>
        """
        
        # Log successful response
        logger.info(f"Successfully generated response for {http_method} {path}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Cache-Control': 'no-cache',
                'X-Service-Status': 'healthy'
            },
            'body': html_content
        }
        
    except Exception as e:
        # Log the error
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Return error response with vague messaging
        error_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CloudTech Solutions - Service Status</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem 0; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 0 2rem; }}
                .nav {{ display: flex; justify-content: space-between; align-items: center; }}
                .logo {{ font-size: 1.5rem; font-weight: bold; }}
                .main {{ padding: 3rem 0; }}
                .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 2rem; margin-bottom: 2rem; }}
                .status-badge {{ display: inline-block; background: #ef4444; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; }}
                .error-content {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 1.5rem; margin-top: 1rem; }}
                .footer {{ background: #1e293b; color: #94a3b8; text-align: center; padding: 2rem 0; }}
                .btn {{ display: inline-block; background: #667eea; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 6px; margin-top: 1rem; }}
            </style>
        </head>
        <body>
            <header class="header">
                <div class="container">
                    <nav class="nav">
                        <div class="logo">CloudTech Solutions</div>
                        <div>API Gateway v2.1.4</div>
                    </nav>
                </div>
            </header>
            
            <main class="main">
                <div class="container">
                    <div class="card">
                        <h1>Service Status</h1>
                        <p><span class="status-badge">⚠ Service Degraded</span></p>
                        
                        <div class="error-content">
                            <h3>We're experiencing technical difficulties</h3>
                            <p>Our team has been notified and is working to resolve the issue. Please try again in a few minutes.</p>
                            <p><strong>Incident ID:</strong> {context.aws_request_id if context else 'INC-' + str(int(time.time()))}</p>
                            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        </div>
                    </div>
                </div>
            </main>
            
            <footer class="footer">
                <div class="container">
                    <p>&copy; 2024 CloudTech Solutions. All rights reserved. | Support: support@cloudtech.com</p>
                </div>
            </footer>
        </body>
        </html>
        """
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/html',
                'X-Service-Status': 'error'
            },
            'body': error_html
        }
