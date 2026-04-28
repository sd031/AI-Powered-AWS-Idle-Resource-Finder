from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import boto3
import json
from datetime import datetime, timedelta
import io
import csv
from .aws_analyzer import AWSResourceAnalyzer
from .ai_filter import AIResourceFilter
from .bedrock_filter import BedrockResourceFilter
import os

app = FastAPI(title="AWS Idle Resource Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AWSCredentials(BaseModel):
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None
    region: Optional[str] = "us-east-1"

class ProfileRequest(BaseModel):
    profile_name: str

class AnalysisRequest(BaseModel):
    credentials: Optional[AWSCredentials] = None
    profile_name: Optional[str] = None
    regions: Optional[List[str]] = None
    enable_ai_filter: Optional[bool] = False
    ai_provider: Optional[str] = "ollama"  # "ollama" or "bedrock"

@app.get("/")
async def root():
    return {"message": "AWS Idle Resource Finder API", "version": "1.0.0"}

@app.get("/profiles")
async def list_profiles():
    try:
        import configparser
        import os
        
        aws_config_path = os.path.expanduser("~/.aws/credentials")
        if not os.path.exists(aws_config_path):
            return {"profiles": []}
        
        config = configparser.ConfigParser()
        config.read(aws_config_path)
        profiles = [section for section in config.sections()]
        
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/regions")
async def list_regions():
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        regions = ec2.describe_regions()
        region_list = [region['RegionName'] for region in regions['Regions']]
        return {"regions": sorted(region_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/status")
async def check_ai_status():
    try:
        # Check Ollama
        ollama_filter = AIResourceFilter()
        ollama_available = await ollama_filter.check_ollama_available()
        
        # Check Bedrock
        bedrock_filter = BedrockResourceFilter()
        bedrock_available = bedrock_filter.check_bedrock_available()
        
        return {
            "providers": {
                "ollama": {
                    "available": ollama_available,
                    "model": "llama3.2:latest",
                    "status": "ready" if ollama_available else "not_available"
                },
                "bedrock": {
                    "available": bedrock_available,
                    "model": "claude-3.5-sonnet",
                    "status": "ready" if bedrock_available else "not_available"
                }
            },
            "available": ollama_available or bedrock_available,
            "default_provider": "bedrock" if bedrock_available else "ollama"
        }
    except Exception as e:
        return {
            "providers": {
                "ollama": {"available": False, "status": "error"},
                "bedrock": {"available": False, "status": "error"}
            },
            "available": False,
            "error": str(e)
        }

@app.post("/analyze")
async def analyze_resources(request: AnalysisRequest):
    try:
        print(f"DEBUG: Received analysis request")
        print(f"DEBUG: profile_name = {request.profile_name}")
        print(f"DEBUG: credentials = {'provided' if request.credentials else 'None'}")
        print(f"DEBUG: regions = {request.regions}")
        print(f"DEBUG: enable_ai_filter = {request.enable_ai_filter}")
        
        analyzer = AWSResourceAnalyzer(
            credentials=request.credentials.dict() if request.credentials else None,
            profile_name=request.profile_name,
            regions=request.regions
        )
        
        results = await analyzer.analyze_all_resources()
        
        if request.enable_ai_filter:
            print(f"DEBUG: ai_provider = {request.ai_provider}")
            
            # Select AI provider
            if request.ai_provider == "bedrock":
                # Use Bedrock with the same session as analyzer
                session = analyzer.session
                print(f"DEBUG: Using session with profile: {request.profile_name}")
                print(f"DEBUG: Session object: {session}")
                ai_filter = BedrockResourceFilter(session=session)
            else:
                # Default to Ollama
                ai_filter = AIResourceFilter()
            
            idle_resources = [
                r for r in results['resources'] 
                if 'Idle' in r.get('recommendation', '') or 
                   'Terminating' in r.get('recommendation', '') or
                   'Low' in r.get('recommendation', '')
            ]
            
            ai_results = await ai_filter.filter_resources(idle_resources, enable_ai=True)
            
            results['ai_filtering'] = {
                'enabled': True,
                'provider': request.ai_provider,
                'total_candidates': len(idle_resources),
                'truly_idle_count': ai_results['truly_idle_count'],
                'ai_model': ai_results.get('ai_model', 'unknown')
            }
            results['resources'] = ai_results['filtered_resources']
            results['idle_resources_count'] = ai_results['truly_idle_count']
            results['potential_savings'] = round(
                sum(r['monthly_cost_usd'] for r in ai_results['filtered_resources']), 2
            )
        else:
            results['ai_filtering'] = {
                'enabled': False
            }
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/csv")
async def export_csv(data: Dict):
    try:
        output = io.StringIO()
        
        if not data.get('resources'):
            raise HTTPException(status_code=400, detail="No resources to export")
        
        resources = data['resources']
        if not resources:
            raise HTTPException(status_code=400, detail="Empty resources list")
        
        has_ai_analysis = any('ai_analysis' in r for r in resources)
        
        if has_ai_analysis:
            fieldnames = ['region', 'resource_type', 'resource_id', 'resource_name', 
                         'state', 'monthly_cost_usd', 'cpu_utilization_avg', 
                         'recommendation', 'ai_confidence', 'ai_reasoning', 'created_date']
        else:
            fieldnames = ['region', 'resource_type', 'resource_id', 'resource_name', 
                         'state', 'monthly_cost_usd', 'cpu_utilization_avg', 
                         'recommendation', 'created_date']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for resource in resources:
            row = {
                'region': resource.get('region', ''),
                'resource_type': resource.get('resource_type', ''),
                'resource_id': resource.get('resource_id', ''),
                'resource_name': resource.get('resource_name', ''),
                'state': resource.get('state', ''),
                'monthly_cost_usd': resource.get('monthly_cost_usd', 0),
                'cpu_utilization_avg': resource.get('cpu_utilization_avg', 0),
                'recommendation': resource.get('recommendation', ''),
                'created_date': resource.get('created_date', '')
            }
            
            if has_ai_analysis and 'ai_analysis' in resource:
                ai = resource['ai_analysis']
                row['ai_confidence'] = f"{ai.get('ai_confidence', 0)}%"
                row['ai_reasoning'] = ai.get('ai_reasoning', '')
            
            writer.writerow(row)
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=aws_resources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
