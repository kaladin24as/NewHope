# Cloud Deployment Guide

## Overview

AntiGravity projects can be deployed to AWS, GCP, or Azure with a single command. The deployment system creates production-ready infrastructure including:

- **Container orchestration** (ECS/GKE/AKS)
- **Managed databases** (RDS/Cloud SQL/Azure SQL)
- **Object storage** (S3/GCS/Blob Storage)
- **Load balancers** and networking
- **Monitoring** and logging
- **Auto-scaling** capabilities

---

## Prerequisites

### AWS Deployment

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure

# Install boto3
pip install boto3
```

### GCP Deployment

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Install Python dependencies
pip install google-cloud-container google-cloud-sql google-cloud-storage google-cloud-secret-manager google-cloud-monitoring
```

### Azure Deployment

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Install Python dependencies
pip install azure-mgmt-resource azure-mgmt-containerservice azure-mgmt-containerregistry azure-mgmt-sql azure-mgmt-storage azure-mgmt-monitor azure-identity
```

---

## Quick Start

### AWS Deployment

```python
from pathlib import Path
from core.deployers.aws_deployer import AWSDeployer

deployer = AWSDeployer(
    project_path=Path("./my_data_project"),
    environment="prod",
    region="us-east-1"
)

result = deployer.deploy(
    vpc_cidr="10.0.0.0/16",
    create_rds=True,
    create_s3=True,
    enable_monitoring=True
)

if result.is_success():
    print(f"✅ Deployed! Application: {result.endpoints['application']}")
    print(f"Database: {result.endpoints['database']}")
else:
    print(f"❌ Deployment failed: {result.message}")
```

### GCP Deployment

```python
from pathlib import Path
from core.deployers.gcp_deployer import GCPDeployer

deployer = GCPDeployer(
    project_path=Path("./my_data_project"),
    environment="prod",
    project_id="my-gcp-project",
    region="us-central1"
)

result = deployer.deploy(
    cluster_size=3,
    create_cloud_sql=True,
    create_gcs=True,
    enable_monitoring=True
)

if result.is_success():
    print(f"✅ Deployed! Application: {result.endpoints['application']}")
```

### Azure Deployment

```python
from pathlib import Path
from core.deployers.azure_deployer import AzureDeployer

deployer = AzureDeployer(
    project_path=Path("./my_data_project"),
    environment="prod",
    subscription_id="your-subscription-id",
    resource_group="antigravity-prod-rg",
    location="eastus"
)

result = deployer.deploy(
    node_count=3,
    create_sql=True,
    create_storage=True,
    enable_monitoring=True
)

if result.is_success():
    print(f"✅ Deployed! Application: {result.endpoints['application']}")
```

---

## Architecture

### AWS Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      VPC (10.0.0.0/16)                  │
│                                                         │
│  ┌───────────────────┐      ┌───────────────────┐     │
│  │  Public Subnets   │      │  Private Subnets  │     │
│  │                   │      │                   │     │
│  │  ┌─────────────┐  │      │  ┌──────────────┐ │     │
│  │  │    ALB      │  │      │  │  ECS Tasks   │ │     │
│  │  └─────────────┘  │      │  └──────────────┘ │     │
│  │                   │      │                   │     │
│  └───────────────────┘      │  ┌──────────────┐ │     │
│                             │  │     RDS      │ │     │
│                             │  └──────────────┘ │     │
│                             └───────────────────┘     │
└─────────────────────────────────────────────────────────┘
         │                              │
         │                              │
    ┌─────────┐                   ┌──────────┐
    │   ECR   │                   │    S3    │
    └─────────┘                   └──────────┘
```

### GCP Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     GKE Cluster                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Kubernetes Services                 │  │
│  │                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │   Pod    │  │   Pod    │  │   Pod    │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘      │  │
│  │                                                  │  │
│  │                Load Balancer                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                              │
         │                              │
    ┌─────────┐                   ┌──────────┐
    │   GCR   │                   │   GCS    │
    └─────────┘                   └──────────┘
         │
    ┌──────────────┐
    │  Cloud SQL   │
    └──────────────┘
```

### Azure Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AKS Cluster                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Kubernetes Services                 │  │
│  │                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │   Pod    │  │   Pod    │  │   Pod    │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘      │  │
│  │                                                  │  │
│  │                Load Balancer                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                              │
         │                              │
    ┌─────────┐                   ┌──────────────┐
    │   ACR   │                   │ Blob Storage │
    └─────────┘                   └──────────────┘
         │
    ┌──────────────┐
    │  Azure SQL   │
    └──────────────┘
```

---

## Deployment Options

### Dry Run

Test deployment without creating resources:

```python
result = deployer.deploy(dry_run=True)
```

### Custom Configuration

#### AWS

```python
deployer.deploy(
    vpc_cidr="10.1.0.0/16",                # Custom VPC CIDR
    create_rds=True,                       # Create RDS database
    create_s3=True,                        # Create S3 bucket
    enable_monitoring=True                 # Enable CloudWatch
)
```

#### GCP

```python
deployer.deploy(
    cluster_size=5,                        # Number of GKE nodes
    create_cloud_sql=True,                 # Create Cloud SQL
    create_gcs=True,                       # Create GCS bucket
    enable_monitoring=True                 # Enable Cloud Monitoring
)
```

#### Azure

```python
deployer.deploy(
    node_count=5,                          # Number of AKS nodes
    create_sql=True,                       # Create Azure SQL
    create_storage=True,                   # Create Storage Account
    enable_monitoring=True                 # Enable Azure Monitor
)
```

---

## Monitoring & Observability

### AWS CloudWatch

After deployment, access monitoring at:
```
https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={project}-{env}-dashboard
```

Metrics available:
- ECS CPU/Memory utilization
- RDS performance metrics
- ALB request counts
- Application logs

### GCP Cloud Monitoring

Access via GCP Console:
- Kubernetes metrics
- Cloud SQL performance
- Application logs in Cloud Logging
- Custom dashboards

### Azure Monitor

Access via Azure Portal:
- AKS cluster metrics
- Azure SQL performance
- Application Insights
- Log Analytics

---

## Scaling

### AWS (ECS)

```python
# Update ECS service desired count
ecs = boto3.client('ecs')
ecs.update_service(
    cluster='my-cluster',
    service='my-service',
    desiredCount=5
)
```

### GCP (GKE)

```bash
# Scale deployment
kubectl scale deployment app --replicas=5

# Enable autoscaling
kubectl autoscale deployment app --min=2 --max=10 --cpu-percent=70
```

### Azure (AKS)

```bash
# Scale deployment
kubectl scale deployment app --replicas=5

# Enable autoscaling
kubectl autoscale deployment app --min=2 --max=10 --cpu-percent=70
```

---

## Destroying Resources

### AWS

```python
result = deployer.destroy()
```

This will:
- Delete ECS cluster and services
- Terminate RDS instance
- Remove S3 bucket (if empty)
- Delete VPC and networking

### GCP

```python
result = deployer.destroy()
```

This will:
- Delete GKE cluster
- Remove Cloud SQL instance
- Delete GCS bucket
- Remove Container Registry images

### Azure

```python
result = deployer.destroy()
```

This will delete the entire resource group, including:
- AKS cluster
- Azure SQL Database
- Storage Account
- All networking resources

---

## Cost Estimation

### AWS

**Minimum (Development):**
- ECS Fargate: ~$30/month (1 task, 0.5 vCPU, 1GB RAM)
- RDS t3.micro: ~$15/month
- ALB: ~$23/month
- **Total:** ~$68/month

**Production:**
- ECS Fargate: ~$120/month (4 tasks)
- RDS t3.small Multi-AZ: ~$70/month
- ALB: ~$23/month
- S3: ~$5/month (100GB)
- **Total:** ~$218/month

### GCP

**Minimum (Development):**
- GKE (3 nodes, e2-medium): ~$75/month
- Cloud SQL (db-f1-micro): ~$10/month
- Load Balancer: ~$20/month
- **Total:** ~$105/month

**Production:**
- GKE (5 nodes, e2-standard-2): ~$190/month
- Cloud SQL (db-n1-standard-1): ~$50/month
- Load Balancer: ~$20/month
- GCS: ~$5/month (100GB)
- **Total:** ~$265/month

### Azure

**Minimum (Development):**
- AKS (3 nodes, Standard_DS2_v2): ~$140/month
- Azure SQL (Basic): ~$5/month
- Load Balancer: ~$20/month
- **Total:** ~$165/month

**Production:**
- AKS (5 nodes, Standard_DS2_v2): ~$230/month
- Azure SQL (Standard S2): ~$75/month
- Load Balancer: ~$20/month
- Blob Storage: ~$5/month (100GB)
- **Total:** ~$330/month

---

## Troubleshooting

### Common Issues

**1. Deployment Timeout**
- Cluster creation can take 10-15 minutes
- RDS/Cloud SQL can take 5-10 minutes
- Be patient and monitor logs

**2. Authentication Errors**
- Verify cloud CLI is installed and configured
- Check credentials have necessary permissions
- Ensure project/subscription IDs are correct

**3. Resource Limits**
- Check account quotas in cloud console
- Request limit increases if needed
- Consider smaller initial deployments

**4. Networking Issues**
- Verify VPC/VNet CIDR doesn't conflict
- Check security group/firewall rules
- Ensure DNS is properly configured

---

## Best Practices

### ✅ Do's

- Use separate accounts/projects for dev/staging/prod
- Enable encryption for all storage
- Use managed databases for production
- Implement auto-scaling
- Set up monitoring and alerts
- Use Infrastructure as Code (Terraform)
- Tag all resources appropriately
- Implement backup strategies

### ❌ Don'ts

- Don't hardcode credentials
- Don't deploy without monitoring
- Don't skip dry-run validation
- Don't ignore cost optimization
- Don't use default passwords
- Don't forget to destroy unused resources
- Don't deploy untested code to production

---

## Next Steps

1. **Review** the generated infrastructure
2. **Test** the deployment in staging
3. **Configure** CI/CD pipelines
4. **Set up** monitoring and alerts
5. **Document** custom configurations
6. **Train** team on deployment process

---

**Need help?** Check the logs or contact support.
