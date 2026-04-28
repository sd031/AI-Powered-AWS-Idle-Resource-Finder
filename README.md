# 🔍 AI-Powered AWS Idle Resource Finder

> A comprehensive CLI and Web application to analyze AWS resources across all regions, identify underutilized or idle resources, and estimate potential cost savings with AI-powered intelligent filtering.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)

---

## 📚 Documentation

**📖 Full Project Guide**: [https://www.learnxops.com/project-ai-powered-aws-idle-resource-finder/](https://www.learnxops.com/project-ai-powered-aws-idle-resource-finder/)

---

## ✨ Features

### Core Capabilities

- 🌍 **Multi-Region Analysis** - Scan all AWS regions or select specific ones
- 💰 **Cost Estimation** - Calculate monthly costs for EC2, RDS, EBS, and Load Balancers
- 📊 **Utilization Metrics** - Track CPU utilization and identify idle resources
- 🎯 **Smart Recommendations** - Get actionable insights on resource optimization
- 📥 **CSV Export** - Export analysis results for reporting and sharing
- 🔐 **Flexible Authentication** - Support for AWS profiles and direct credentials

---

## 📋 Supported AWS Resources

| Resource Type            | Metrics Tracked        | Cost Estimation             |
| ------------------------ | ---------------------- | --------------------------- |
| **EC2 Instances**  | CPU utilization, state | ✅ On-demand pricing        |
| **RDS Databases**  | CPU utilization, state | ✅ Instance class pricing   |
| **EBS Volumes**    | Attachment status      | ✅ Volume size & type       |
| **Load Balancers** | Active connections     | ✅ Hourly + data processing |

## ⚠️ Disclaimer

This tool provides cost estimates based on standard AWS pricing. Actual costs may vary. Always verify costs using AWS Cost Explorer and billing dashboard before making decisions.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Made with ❤️ for AWS cost optimization**
