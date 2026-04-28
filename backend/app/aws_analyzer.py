import boto3
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AWSResourceAnalyzer:
    def __init__(self, credentials: Optional[Dict] = None, profile_name: Optional[str] = None, regions: Optional[List[str]] = None):
        self.credentials = credentials
        self.profile_name = profile_name
        self.regions = regions or []
        self.session = None
        self._initialize_session()
        
    def _initialize_session(self):
        if self.profile_name:
            self.session = boto3.Session(profile_name=self.profile_name)
        elif self.credentials:
            self.session = boto3.Session(
                aws_access_key_id=self.credentials.get('access_key_id'),
                aws_secret_access_key=self.credentials.get('secret_access_key'),
                aws_session_token=self.credentials.get('session_token')
            )
        else:
            self.session = boto3.Session()
    
    def _get_all_regions(self):
        if self.regions:
            return self.regions
        
        try:
            ec2 = self.session.client('ec2', region_name='us-east-1')
            regions_response = ec2.describe_regions()
            return [region['RegionName'] for region in regions_response['Regions']]
        except Exception as e:
            print(f"Error fetching regions: {e}")
            return ['us-east-1', 'us-west-2', 'eu-west-1']
    
    def _get_ec2_instances(self, region: str) -> List[Dict]:
        try:
            ec2 = self.session.client('ec2', region_name=region)
            cloudwatch = self.session.client('cloudwatch', region_name=region)
            
            instances = ec2.describe_instances()
            resources = []
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    state = instance['State']['Name']
                    
                    name = ''
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                    
                    cpu_utilization = self._get_cpu_utilization(cloudwatch, instance_id)
                    monthly_cost = self._estimate_ec2_cost(instance_type, region)
                    
                    recommendation = self._get_recommendation(cpu_utilization, state)
                    
                    resources.append({
                        'region': region,
                        'resource_type': 'EC2 Instance',
                        'resource_id': instance_id,
                        'resource_name': name or instance_id,
                        'instance_type': instance_type,
                        'state': state,
                        'monthly_cost_usd': monthly_cost,
                        'cpu_utilization_avg': cpu_utilization,
                        'recommendation': recommendation,
                        'created_date': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else ''
                    })
            
            return resources
        except Exception as e:
            print(f"Error analyzing EC2 in {region}: {e}")
            return []
    
    def _get_rds_instances(self, region: str) -> List[Dict]:
        try:
            rds = self.session.client('rds', region_name=region)
            cloudwatch = self.session.client('cloudwatch', region_name=region)
            
            db_instances = rds.describe_db_instances()
            resources = []
            
            for db in db_instances['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                db_class = db['DBInstanceClass']
                status = db['DBInstanceStatus']
                
                cpu_utilization = self._get_rds_cpu_utilization(cloudwatch, db_id)
                monthly_cost = self._estimate_rds_cost(db_class, region)
                
                recommendation = self._get_recommendation(cpu_utilization, status)
                
                resources.append({
                    'region': region,
                    'resource_type': 'RDS Instance',
                    'resource_id': db_id,
                    'resource_name': db_id,
                    'instance_type': db_class,
                    'state': status,
                    'monthly_cost_usd': monthly_cost,
                    'cpu_utilization_avg': cpu_utilization,
                    'recommendation': recommendation,
                    'created_date': db.get('InstanceCreateTime', '').isoformat() if db.get('InstanceCreateTime') else ''
                })
            
            return resources
        except Exception as e:
            print(f"Error analyzing RDS in {region}: {e}")
            return []
    
    def _get_ebs_volumes(self, region: str) -> List[Dict]:
        try:
            ec2 = self.session.client('ec2', region_name=region)
            
            volumes = ec2.describe_volumes()
            resources = []
            
            for volume in volumes['Volumes']:
                volume_id = volume['VolumeId']
                size = volume['Size']
                state = volume['State']
                volume_type = volume['VolumeType']
                
                name = ''
                if 'Tags' in volume:
                    for tag in volume['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                
                monthly_cost = self._estimate_ebs_cost(size, volume_type, region)
                
                recommendation = 'Delete - Unattached' if state == 'available' else 'In Use'
                
                resources.append({
                    'region': region,
                    'resource_type': 'EBS Volume',
                    'resource_id': volume_id,
                    'resource_name': name or volume_id,
                    'instance_type': f"{volume_type} ({size} GB)",
                    'state': state,
                    'monthly_cost_usd': monthly_cost,
                    'cpu_utilization_avg': 0,
                    'recommendation': recommendation,
                    'created_date': volume.get('CreateTime', '').isoformat() if volume.get('CreateTime') else ''
                })
            
            return resources
        except Exception as e:
            print(f"Error analyzing EBS in {region}: {e}")
            return []
    
    def _get_load_balancers(self, region: str) -> List[Dict]:
        try:
            elb = self.session.client('elbv2', region_name=region)
            
            load_balancers = elb.describe_load_balancers()
            resources = []
            
            for lb in load_balancers['LoadBalancers']:
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                state = lb['State']['Code']
                
                monthly_cost = self._estimate_elb_cost(lb_type, region)
                
                resources.append({
                    'region': region,
                    'resource_type': f'{lb_type.upper()} Load Balancer',
                    'resource_id': lb['LoadBalancerArn'].split('/')[-1],
                    'resource_name': lb_name,
                    'instance_type': lb_type,
                    'state': state,
                    'monthly_cost_usd': monthly_cost,
                    'cpu_utilization_avg': 0,
                    'recommendation': 'Review Usage',
                    'created_date': lb.get('CreatedTime', '').isoformat() if lb.get('CreatedTime') else ''
                })
            
            return resources
        except Exception as e:
            print(f"Error analyzing Load Balancers in {region}: {e}")
            return []
    
    def _get_cpu_utilization(self, cloudwatch, instance_id: str) -> float:
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return round(avg_cpu, 2)
            return 0.0
        except Exception as e:
            print(f"Error getting CPU utilization for {instance_id}: {e}")
            return 0.0
    
    def _get_rds_cpu_utilization(self, cloudwatch, db_id: str) -> float:
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return round(avg_cpu, 2)
            return 0.0
        except Exception as e:
            print(f"Error getting CPU utilization for RDS {db_id}: {e}")
            return 0.0
    
    def _estimate_ec2_cost(self, instance_type: str, region: str) -> float:
        pricing_map = {
            't2.micro': 8.35, 't2.small': 16.79, 't2.medium': 33.58,
            't3.micro': 7.59, 't3.small': 15.18, 't3.medium': 30.37,
            'm5.large': 69.35, 'm5.xlarge': 138.70, 'm5.2xlarge': 277.40,
            'c5.large': 61.63, 'c5.xlarge': 123.26, 'c5.2xlarge': 246.53,
        }
        return pricing_map.get(instance_type, 50.0)
    
    def _estimate_rds_cost(self, db_class: str, region: str) -> float:
        pricing_map = {
            'db.t3.micro': 11.52, 'db.t3.small': 23.04, 'db.t3.medium': 46.08,
            'db.m5.large': 104.11, 'db.m5.xlarge': 208.22, 'db.m5.2xlarge': 416.45,
        }
        return pricing_map.get(db_class, 75.0)
    
    def _estimate_ebs_cost(self, size_gb: int, volume_type: str, region: str) -> float:
        cost_per_gb = {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125,
            'st1': 0.045, 'sc1': 0.015, 'standard': 0.05
        }
        return size_gb * cost_per_gb.get(volume_type, 0.10)
    
    def _estimate_elb_cost(self, lb_type: str, region: str) -> float:
        if lb_type == 'application':
            return 16.20 + 5.84
        elif lb_type == 'network':
            return 16.20 + 4.38
        return 18.25
    
    def _get_recommendation(self, cpu_utilization: float, state: str) -> str:
        if state in ['stopped', 'stopping']:
            return 'Consider Terminating - Stopped'
        elif cpu_utilization < 5:
            return 'Idle - Consider Downsizing or Terminating'
        elif cpu_utilization < 20:
            return 'Low Utilization - Consider Downsizing'
        elif cpu_utilization < 50:
            return 'Moderate Utilization'
        else:
            return 'Active - Good Utilization'
    
    def _analyze_region(self, region: str) -> List[Dict]:
        print(f"Analyzing region: {region}")
        resources = []
        
        resources.extend(self._get_ec2_instances(region))
        resources.extend(self._get_rds_instances(region))
        resources.extend(self._get_ebs_volumes(region))
        resources.extend(self._get_load_balancers(region))
        
        return resources
    
    async def analyze_all_resources(self) -> Dict:
        regions = self._get_all_regions()
        all_resources = []
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                loop.run_in_executor(executor, self._analyze_region, region)
                for region in regions
            ]
            results = await asyncio.gather(*futures)
        
        for region_resources in results:
            all_resources.extend(region_resources)
        
        total_cost = sum(r['monthly_cost_usd'] for r in all_resources)
        idle_resources = [r for r in all_resources if 'Idle' in r['recommendation'] or 'Terminating' in r['recommendation']]
        
        return {
            'total_resources': len(all_resources),
            'total_monthly_cost': round(total_cost, 2),
            'idle_resources_count': len(idle_resources),
            'potential_savings': round(sum(r['monthly_cost_usd'] for r in idle_resources), 2),
            'resources': all_resources,
            'analyzed_regions': regions,
            'timestamp': datetime.utcnow().isoformat()
        }
