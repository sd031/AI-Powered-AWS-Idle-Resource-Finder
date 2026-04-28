import boto3
import json
from typing import List, Dict, Optional

class BedrockResourceFilter:
    def __init__(self, session=None, region: str = 'us-east-1'):
        """Initialize Bedrock AI filter with AWS session"""
        self.session = session or boto3.Session()
        self.region = region
        # Use inference profile ARN for on-demand throughput
        # This is the cross-region inference profile for Claude 3.5 Sonnet v2
        self.model_id = "us.anthropic.claude-sonnet-4-6"
        
        try:
            self.bedrock_runtime = self.session.client(
                service_name='bedrock-runtime',
                region_name=self.region
            )
        except Exception as e:
            print(f"Error initializing Bedrock client: {e}")
            self.bedrock_runtime = None
    
    def check_bedrock_available(self) -> bool:
        """Check if Bedrock is available and accessible"""
        if not self.bedrock_runtime:
            return False
        
        try:
            # Try to list foundation models to verify access
            bedrock = self.session.client('bedrock', region_name=self.region)
            response = bedrock.list_foundation_models(
                byProvider='Anthropic'
            )
            models = response.get('modelSummaries', [])
            if len(models) > 0:
                print(f"✓ Bedrock available with {len(models)} Anthropic models")
                return True
            else:
                print("✗ Bedrock: No Anthropic models found. You may need to request model access in AWS Console.")
                return False
        except Exception as e:
            error_name = type(e).__name__
            if 'AccessDenied' in str(e) or 'UnauthorizedOperation' in str(e):
                print(f"✗ Bedrock: Access denied. Enable Bedrock in AWS Console: https://console.aws.amazon.com/bedrock")
            elif 'ResourceNotFound' in str(e):
                print(f"✗ Bedrock: Service not available in {self.region}. Try us-east-1 or us-west-2.")
            else:
                print(f"✗ Bedrock not available: {error_name} - {str(e)[:100]}")
            return False
    
    async def analyze_resource(self, resource: Dict) -> Dict:
        """Use Bedrock Claude to analyze if a resource is truly idle"""
        if not self.bedrock_runtime:
            return self._fallback_analysis(resource)
        
        prompt = self._create_analysis_prompt(resource)
        
        try:
            # Prepare the request for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text'].strip()
            
            # Parse AI decision
            is_truly_idle = self._parse_ai_response(ai_response)
            confidence = self._extract_confidence(ai_response)
            reasoning = self._extract_reasoning(ai_response)
            
            return {
                'is_truly_idle': is_truly_idle,
                'ai_confidence': confidence,
                'ai_reasoning': reasoning,
                'original_recommendation': resource.get('recommendation', ''),
                'ai_provider': 'bedrock-claude'
            }
            
        except Exception as e:
            error_name = type(e).__name__
            if error_name == 'ResourceNotFoundException':
                # Model not available - only print once
                if not hasattr(self, '_model_error_shown'):
                    print(f"⚠️  Bedrock model '{self.model_id}' not found.")
                    print(f"    → Enable model access at: https://console.aws.amazon.com/bedrock/home?region={self.region}#/modelaccess")
                    print(f"    → Using fallback analysis for all resources")
                    self._model_error_shown = True
            elif error_name == 'ValidationException':
                # Show detailed validation error - only once
                if not hasattr(self, '_validation_error_shown'):
                    print(f"⚠️  Bedrock ValidationException:")
                    print(f"    Model ID: {self.model_id}")
                    print(f"    Error: {str(e)}")
                    print(f"    → Using fallback analysis for all resources")
                    self._validation_error_shown = True
            else:
                print(f"Bedrock AI error for {resource.get('resource_id')} ({error_name}): {str(e)[:200]}, using fallback")
            return self._fallback_analysis(resource)
    
    def _create_analysis_prompt(self, resource: Dict) -> str:
        """Create a detailed prompt for AI analysis"""
        return f"""You are an AWS cost optimization expert. Analyze this resource and determine if it's TRULY idle and should be terminated or downsized.

Resource Details:
- Type: {resource.get('resource_type', 'Unknown')}
- Name: {resource.get('resource_name', 'Unknown')}
- State: {resource.get('state', 'Unknown')}
- CPU Utilization (7-day avg): {resource.get('cpu_utilization_avg', 0)}%
- Monthly Cost: ${resource.get('monthly_cost_usd', 0):.2f}
- Instance Type: {resource.get('instance_type', 'N/A')}
- Created: {resource.get('created_date', 'Unknown')}
- Current Recommendation: {resource.get('recommendation', 'Unknown')}

Consider these factors:
1. CPU utilization patterns - is low CPU justified for this resource type?
2. Resource state and configuration
3. Potential roles: backup, DR, standby, scheduled workloads
4. Cost vs utilization ratio
5. Resource type characteristics (databases need different thresholds than compute)

Respond in EXACTLY this format:
DECISION: [TRULY_IDLE or NOT_IDLE]
CONFIDENCE: [0-100]%
REASONING: [Brief 1-2 sentence explanation]

Be conservative - only mark as TRULY_IDLE if you're confident it serves no purpose."""

    def _parse_ai_response(self, response: str) -> bool:
        """Parse AI response to determine if resource is truly idle"""
        response_lower = response.lower()
        
        # Look for decision line
        if 'decision:' in response_lower:
            decision_line = [line for line in response.split('\n') if 'decision:' in line.lower()]
            if decision_line:
                return 'truly_idle' in decision_line[0].lower() or 'truly idle' in decision_line[0].lower()
        
        # Fallback: look for keywords
        return 'truly_idle' in response_lower or 'truly idle' in response_lower
    
    def _extract_confidence(self, response: str) -> int:
        """Extract confidence percentage from AI response"""
        try:
            # Look for CONFIDENCE: XX%
            for line in response.split('\n'):
                if 'confidence:' in line.lower():
                    # Extract number
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        confidence = int(numbers[0])
                        return min(max(confidence, 0), 100)  # Clamp to 0-100
        except:
            pass
        
        # Default confidence
        return 70
    
    def _extract_reasoning(self, response: str) -> str:
        """Extract reasoning from AI response"""
        try:
            # Look for REASONING: line
            for i, line in enumerate(response.split('\n')):
                if 'reasoning:' in line.lower():
                    reasoning = line.split(':', 1)[1].strip()
                    # Get next lines if reasoning continues
                    lines = response.split('\n')
                    if i + 1 < len(lines) and not lines[i + 1].startswith(('DECISION', 'CONFIDENCE')):
                        reasoning += ' ' + lines[i + 1].strip()
                    return reasoning[:200]  # Limit length
        except:
            pass
        
        # Fallback: return first sentence
        sentences = response.split('.')
        if sentences:
            return sentences[0][:200]
        
        return "AI analysis completed"
    
    def _fallback_analysis(self, resource: Dict) -> Dict:
        """Fallback to rule-based analysis if AI fails"""
        recommendation = resource.get('recommendation', '').lower()
        cpu = resource.get('cpu_utilization_avg', 0)
        
        # Simple rule-based decision
        is_idle = (
            'idle' in recommendation or
            'terminating' in recommendation or
            (cpu < 5 and 'stopped' not in resource.get('state', '').lower())
        )
        
        confidence = 60 if is_idle else 50
        reasoning = f"Rule-based: {recommendation}, CPU {cpu}%"
        
        return {
            'is_truly_idle': is_idle,
            'ai_confidence': confidence,
            'ai_reasoning': reasoning,
            'original_recommendation': resource.get('recommendation', ''),
            'ai_provider': 'fallback'
        }
    
    async def filter_resources(self, resources: List[Dict], enable_ai: bool = True) -> Dict:
        """Filter resources using Bedrock AI"""
        if not enable_ai or not self.bedrock_runtime:
            return {
                'filtered_resources': resources,
                'truly_idle_count': len(resources),
                'ai_model': 'disabled'
            }
        
        truly_idle_resources = []
        
        for resource in resources:
            analysis = await self.analyze_resource(resource)
            
            if analysis['is_truly_idle']:
                # Add AI analysis to resource
                resource['ai_analysis'] = {
                    'ai_confidence': analysis['ai_confidence'],
                    'ai_reasoning': analysis['ai_reasoning'],
                    'ai_provider': analysis.get('ai_provider', 'bedrock-claude')
                }
                truly_idle_resources.append(resource)
        
        return {
            'filtered_resources': truly_idle_resources,
            'truly_idle_count': len(truly_idle_resources),
            'ai_model': self.model_id
        }
