#!/usr/bin/env python3
import argparse
import asyncio
import json
import csv
import sys
from datetime import datetime
from app.aws_analyzer import AWSResourceAnalyzer

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════╗
║         AWS Idle Resource Finder - CLI Tool               ║
║         Find underutilized AWS resources                  ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_summary(results):
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Resources Found: {results['total_resources']}")
    print(f"Total Monthly Cost: ${results['total_monthly_cost']:.2f}")
    print(f"Idle Resources: {results['idle_resources_count']}")
    print(f"Potential Monthly Savings: ${results['potential_savings']:.2f}")
    print(f"Regions Analyzed: {', '.join(results['analyzed_regions'])}")
    print("="*60 + "\n")

def print_resources_table(resources):
    if not resources:
        print("No resources found.")
        return
    
    print("\n" + "="*150)
    print(f"{'Region':<15} {'Type':<20} {'Name':<25} {'State':<12} {'Cost/Mo':<10} {'CPU%':<8} {'Recommendation':<30}")
    print("="*150)
    
    for resource in resources:
        print(f"{resource['region']:<15} "
              f"{resource['resource_type']:<20} "
              f"{resource['resource_name'][:24]:<25} "
              f"{resource['state']:<12} "
              f"${resource['monthly_cost_usd']:<9.2f} "
              f"{resource['cpu_utilization_avg']:<7.1f}% "
              f"{resource['recommendation']:<30}")
    
    print("="*150 + "\n")

def export_to_csv(resources, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['region', 'resource_type', 'resource_id', 'resource_name', 
                         'state', 'monthly_cost_usd', 'cpu_utilization_avg', 
                         'recommendation', 'created_date']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for resource in resources:
                writer.writerow({
                    'region': resource.get('region', ''),
                    'resource_type': resource.get('resource_type', ''),
                    'resource_id': resource.get('resource_id', ''),
                    'resource_name': resource.get('resource_name', ''),
                    'state': resource.get('state', ''),
                    'monthly_cost_usd': resource.get('monthly_cost_usd', 0),
                    'cpu_utilization_avg': resource.get('cpu_utilization_avg', 0),
                    'recommendation': resource.get('recommendation', ''),
                    'created_date': resource.get('created_date', '')
                })
        
        print(f"✓ Data exported to: {filename}")
    except Exception as e:
        print(f"✗ Error exporting to CSV: {e}")
        sys.exit(1)

def export_to_json(results, filename):
    try:
        with open(filename, 'w') as jsonfile:
            json.dump(results, jsonfile, indent=2)
        
        print(f"✓ Data exported to: {filename}")
    except Exception as e:
        print(f"✗ Error exporting to JSON: {e}")
        sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(
        description='AWS Idle Resource Finder - Analyze AWS resources for cost optimization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze using default AWS credentials
  python cli.py
  
  # Analyze using a specific AWS profile
  python cli.py --profile production
  
  # Analyze specific regions only
  python cli.py --regions us-east-1 us-west-2
  
  # Export results to CSV
  python cli.py --profile dev --export-csv results.csv
  
  # Show only idle resources
  python cli.py --idle-only
        """
    )
    
    parser.add_argument('--profile', '-p', 
                       help='AWS profile name to use from ~/.aws/credentials')
    
    parser.add_argument('--access-key', 
                       help='AWS Access Key ID')
    
    parser.add_argument('--secret-key', 
                       help='AWS Secret Access Key')
    
    parser.add_argument('--session-token', 
                       help='AWS Session Token (for temporary credentials)')
    
    parser.add_argument('--regions', '-r', nargs='+',
                       help='Specific AWS regions to analyze (default: all regions)')
    
    parser.add_argument('--export-csv', metavar='FILE',
                       help='Export results to CSV file')
    
    parser.add_argument('--export-json', metavar='FILE',
                       help='Export results to JSON file')
    
    parser.add_argument('--idle-only', action='store_true',
                       help='Show only idle/underutilized resources')
    
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output (no banner or table)')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    credentials = None
    if args.access_key and args.secret_key:
        credentials = {
            'access_key_id': args.access_key,
            'secret_access_key': args.secret_key,
            'session_token': args.session_token
        }
    
    try:
        if not args.quiet:
            print("🔍 Starting AWS resource analysis...")
            if args.profile:
                print(f"   Using AWS Profile: {args.profile}")
            if args.regions:
                print(f"   Analyzing Regions: {', '.join(args.regions)}")
            else:
                print("   Analyzing All Regions")
            print()
        
        analyzer = AWSResourceAnalyzer(
            credentials=credentials,
            profile_name=args.profile,
            regions=args.regions
        )
        
        results = await analyzer.analyze_all_resources()
        
        if args.idle_only:
            results['resources'] = [
                r for r in results['resources'] 
                if 'Idle' in r['recommendation'] or 'Terminating' in r['recommendation']
            ]
        
        if not args.quiet:
            print_summary(results)
            print_resources_table(results['resources'])
        
        if args.export_csv:
            export_to_csv(results['resources'], args.export_csv)
        
        if args.export_json:
            export_to_json(results, args.export_json)
        
        if args.quiet and not args.export_csv and not args.export_json:
            print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
