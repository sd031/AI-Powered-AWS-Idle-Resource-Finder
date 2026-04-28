import httpx
import json
import os
from typing import List, Dict, Optional

class AIResourceFilter:
    def __init__(self, ollama_host: str = None):
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        self.model = "llama3.2:latest"
        
    async def check_ollama_available(self) -> bool:
        """Check if Ollama is available and model is pulled"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_available = any(m['name'] == self.model for m in models)
                    
                    # Warm up the model with a quick test if available
                    if model_available:
                        print("Warming up AI model...")
                        try:
                            await self._warmup_model()
                        except Exception as e:
                            print(f"Model warmup failed: {e}")
                    
                    return model_available
                return False
        except Exception as e:
            print(f"Error checking Ollama: {e}")
            return False
    
    async def _warmup_model(self):
        """Warm up the model with a quick test inference"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": "Say 'ready' in one word.",
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                if response.status_code == 200:
                    print("AI model warmed up successfully")
                    return True
        except Exception as e:
            print(f"Warmup error: {e}")
            return False
    
    async def pull_model_if_needed(self) -> bool:
        """Pull the Llama model if not already available"""
        try:
            if await self.check_ollama_available():
                return True
            
            print(f"Pulling {self.model} model... This may take a few minutes.")
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/pull",
                    json={"name": self.model}
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
    
    async def analyze_resource(self, resource: Dict) -> Dict:
        """Use AI to analyze if a resource is truly idle"""
        prompt = self._create_analysis_prompt(resource)
        
        try:
            # Use 60s timeout - if model is warmed up, this should be enough
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('response', '').strip().lower()
                    
                    is_truly_idle = self._parse_ai_response(ai_response)
                    confidence = self._extract_confidence(ai_response)
                    reasoning = self._extract_reasoning(ai_response)
                    
                    return {
                        'is_truly_idle': is_truly_idle,
                        'ai_confidence': confidence,
                        'ai_reasoning': reasoning,
                        'original_recommendation': resource.get('recommendation', '')
                    }
                else:
                    return self._fallback_analysis(resource)
                    
        except Exception as e:
            error_msg = f"AI timeout for {resource.get('resource_id')} ({type(e).__name__}), using fallback"
            print(error_msg)
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
- Current Recommendation: {resource.get('recommendation', 'None')}
- Created: {resource.get('created_date', 'Unknown')}

Consider these factors:
1. CPU utilization patterns (very low usage might indicate idle, but some resources are meant to be on standby)
2. Resource state (stopped resources still cost money for EBS)
3. Resource type (databases, load balancers, etc. have different usage patterns)
4. Cost vs utilization ratio
5. Whether this could be a backup, disaster recovery, or standby resource
6. Development/testing resources that might be intentionally idle

Respond in this exact format:
DECISION: [TRULY_IDLE or NOT_IDLE]
CONFIDENCE: [0-100]%
REASONING: [Brief explanation in one sentence]

Example responses:
DECISION: TRULY_IDLE
CONFIDENCE: 95%
REASONING: EC2 instance with 2% CPU for 7 days and no special tags suggests it's forgotten and wasting money.

DECISION: NOT_IDLE
CONFIDENCE: 80%
REASONING: Load balancer with low traffic might be serving critical but infrequent requests.

Now analyze the resource above:"""
    
    def _parse_ai_response(self, response: str) -> bool:
        """Parse AI response to determine if resource is truly idle"""
        if 'truly_idle' in response or 'decision: truly_idle' in response:
            return True
        elif 'not_idle' in response or 'decision: not_idle' in response:
            return False
        
        if 'terminate' in response or 'delete' in response or 'remove' in response:
            return True
        
        return False
    
    def _extract_confidence(self, response: str) -> int:
        """Extract confidence percentage from AI response"""
        try:
            if 'confidence:' in response:
                confidence_part = response.split('confidence:')[1].split('\n')[0]
                confidence_str = ''.join(filter(str.isdigit, confidence_part))
                if confidence_str:
                    return min(int(confidence_str), 100)
        except:
            pass
        return 70
    
    def _extract_reasoning(self, response: str) -> str:
        """Extract reasoning from AI response"""
        try:
            if 'reasoning:' in response:
                reasoning = response.split('reasoning:')[1].split('\n')[0].strip()
                return reasoning[:200]
        except:
            pass
        return "AI analysis completed"
    
    def _fallback_analysis(self, resource: Dict) -> Dict:
        """Fallback analysis when AI is not available"""
        cpu = resource.get('cpu_utilization_avg', 0)
        state = resource.get('state', '').lower()
        recommendation = resource.get('recommendation', '').lower()
        
        is_truly_idle = (
            cpu < 3 or 
            state in ['stopped', 'stopping'] or
            'terminate' in recommendation or
            'unattached' in recommendation
        )
        
        return {
            'is_truly_idle': is_truly_idle,
            'ai_confidence': 60,
            'ai_reasoning': 'Fallback rule-based analysis (AI unavailable)',
            'original_recommendation': resource.get('recommendation', '')
        }
    
    async def filter_resources(self, resources: List[Dict], enable_ai: bool = True) -> Dict:
        """Filter resources using AI analysis"""
        if not enable_ai:
            return {
                'filtered_resources': resources,
                'ai_enabled': False,
                'total_analyzed': len(resources),
                'truly_idle_count': 0
            }
        
        if not await self.check_ollama_available():
            await self.pull_model_if_needed()
        
        filtered_resources = []
        truly_idle_count = 0
        
        for resource in resources:
            ai_analysis = await self.analyze_resource(resource)
            
            resource_with_ai = {
                **resource,
                'ai_analysis': ai_analysis
            }
            
            if ai_analysis['is_truly_idle']:
                filtered_resources.append(resource_with_ai)
                truly_idle_count += 1
        
        return {
            'filtered_resources': filtered_resources,
            'ai_enabled': True,
            'total_analyzed': len(resources),
            'truly_idle_count': truly_idle_count,
            'ai_model': self.model
        }
