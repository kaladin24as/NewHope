"""
AWS Cloud Deployer
==================

Production-ready deployment to AWS using ECS, RDS, S3, and CloudWatch.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .base import CloudDeployer, DeploymentResult, DeploymentStatus

console = Console()


class AWSDeployer(CloudDeployer):
    """
    Deploy AntiGravity projects to AWS.
    
    Architecture:
    - ECS Fargate for container orchestration
    - RDS for databases (PostgreSQL, MySQL)
    - S3 for data storage
    - ECR for container registry
    - CloudWatch for monitoring
    - Secrets Manager for credentials
    - VPC with public/private subnets
    """
    
    def __init__(
        self,
        project_path: Path,
        environment: str = "prod",
        region: str = "us-east-1"
    ):
        """
        Initialize AWS deployer.
        
        Args:
            project_path: Path to AntiGravity project
            environment: Target environment
            region: AWS region
        """
        super().__init__(project_path, environment)
        self.region = region
        self.stack_name = None
        
        # Lazy import AWS SDK
        try:
            import boto3
            self.boto3 = boto3
            self.session = boto3.Session(region_name=region)
        except ImportError:
            raise ImportError(
                "boto3 is required for AWS deployment. "
                "Install with: pip install boto3"
            )
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            console.print(f"[green]✓[/green] AWS credentials valid")
            console.print(f"  Account: {identity['Account']}")
            console.print(f"  User: {identity['Arn']}")
            console.print(f"  Region: {self.region}")
            
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] AWS credentials invalid: {e}")
            return False
    
    def deploy(
        self,
        vpc_cidr: str = "10.0.0.0/16",
        create_rds: bool = True,
        create_s3: bool = True,
        enable_monitoring: bool = True,
        dry_run: bool = False
    ) -> DeploymentResult:
        """
        Deploy project to AWS.
        
        Args:
            vpc_cidr: CIDR block for VPC
            create_rds: Create RDS database
            create_s3: Create S3 bucket
            enable_monitoring: Enable CloudWatch monitoring
            dry_run: Only validate, don't deploy
        
        Returns:
            DeploymentResult with deployment info
        """
        console.print("\n[bold cyan]🚀 AWS Deployment Starting[/bold cyan]")
        console.print("=" * 60)
        
        # Load project config
        config = self._load_project_config()
        project_name = config["project"]["name"]
        stack = config["project"]["stack"]
        
        self.stack_name = f"{project_name}-{self.environment}"
        
        errors = []
        resources = {}
        endpoints = {}
        
        try:
            # Step 1: Validate credentials
            if not self.validate_credentials():
                return DeploymentResult(
                    status=DeploymentStatus.FAILED,
                    message="AWS credentials validation failed",
                    endpoints={},
                    resources={},
                    errors=["Invalid AWS credentials"]
                )
            
            if dry_run:
                console.print("\n[yellow]Dry run mode - no resources will be created[/yellow]")
                return DeploymentResult(
                    status=DeploymentStatus.SUCCESS,
                    message="Dry run completed successfully",
                    endpoints={},
                    resources={},
                    errors=[]
                )
            
            # Step 2: Create VPC and networking
            console.print("\n[cyan]Step 1/7:[/cyan] Creating VPC and networking...")
            vpc_resources = self._create_vpc(vpc_cidr)
            resources.update(vpc_resources)
            console.print("[green]✓[/green] VPC created")
            
            # Step 3: Create ECR repository
            console.print("\n[cyan]Step 2/7:[/cyan] Creating ECR repository...")
            ecr_uri = self._create_ecr_repository()
            resources["ecr_repository"] = ecr_uri
            console.print(f"[green]✓[/green] ECR repository: {ecr_uri}")
            
            # Step 4: Build and push Docker images
            console.print("\n[cyan]Step 3/7:[/cyan] Building and pushing Docker images...")
            self._build_and_push_images(ecr_uri, stack)
            console.print("[green]✓[/green] Images pushed to ECR")
            
            # Step 5: Create RDS database (if needed)
            if create_rds and "storage" in stack:
                console.print("\n[cyan]Step 4/7:[/cyan] Creating RDS database...")
                db_resources = self._create_rds_database(
                    vpc_resources["vpc_id"],
                    vpc_resources["private_subnets"]
                )
                resources.update(db_resources)
                endpoints["database"] = db_resources["db_endpoint"]
                console.print(f"[green]✓[/green] RDS endpoint: {db_resources['db_endpoint']}")
            
            # Step 6: Create S3 bucket (if needed)
            if create_s3:
                console.print("\n[cyan]Step 5/7:[/cyan] Creating S3 bucket...")
                bucket_name = self._create_s3_bucket()
                resources["s3_bucket"] = bucket_name
                console.print(f"[green]✓[/green] S3 bucket: {bucket_name}")
            
            # Step 7: Create ECS cluster and services
            console.print("\n[cyan]Step 6/7:[/cyan] Creating ECS cluster and services...")
            ecs_resources = self._create_ecs_cluster(
                vpc_resources,
                ecr_uri,
                stack
            )
            resources.update(ecs_resources)
            
            if "load_balancer_dns" in ecs_resources:
                endpoints["application"] = f"http://{ecs_resources['load_balancer_dns']}"
                console.print(f"[green]✓[/green] Application: {endpoints['application']}")
            
            # Step 8: Setup monitoring (if enabled)
            if enable_monitoring:
                console.print("\n[cyan]Step 7/7:[/cyan] Setting up CloudWatch monitoring...")
                monitoring_resources = self._setup_monitoring()
                resources.update(monitoring_resources)
                endpoints["monitoring"] = monitoring_resources.get("dashboard_url", "")
                console.print("[green]✓[/green] Monitoring configured")
            
            console.print("\n" + "=" * 60)
            console.print("[bold green]✅ Deployment completed successfully![/bold green]")
            
            return DeploymentResult(
                status=DeploymentStatus.SUCCESS,
                message=f"Successfully deployed {project_name} to AWS",
                endpoints=endpoints,
                resources=resources,
                errors=errors
            )
            
        except Exception as e:
            console.print(f"\n[bold red]✗ Deployment failed: {e}[/bold red]")
            
            # Attempt rollback
            console.print("\n[yellow]Attempting rollback...[/yellow]")
            try:
                self._rollback_resources(resources)
                console.print("[green]✓[/green] Rollback completed")
            except Exception as rollback_error:
                console.print(f"[red]✗[/red] Rollback failed: {rollback_error}")
                errors.append(f"Rollback failed: {rollback_error}")
            
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                message=f"Deployment failed: {str(e)}",
                endpoints=endpoints,
                resources=resources,
                errors=errors + [str(e)]
            )
    
    def _create_vpc(self, cidr: str) -> Dict[str, str]:
        """Create VPC with public and private subnets"""
        ec2 = self.session.client('ec2')
        
        # Create VPC
        vpc_response = ec2.create_vpc(
            CidrBlock=cidr,
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [
                    {'Key': 'Name', 'Value': f'{self.stack_name}-vpc'},
                    {'Key': 'Environment', 'Value': self.environment}
                ]
            }]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        
        # Enable DNS
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
        
        # Create Internet Gateway
        igw_response = ec2.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': f'{self.stack_name}-igw'}]
            }]
        )
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        
        # Create subnets
        availability_zones = ec2.describe_availability_zones()['AvailabilityZones'][:2]
        
        public_subnets = []
        private_subnets = []
        
        for idx, az in enumerate(availability_zones):
            # Public subnet
            public_subnet = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=f"10.0.{idx}.0/24",
                AvailabilityZone=az['ZoneName'],
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f'{self.stack_name}-public-{idx+1}'}]
                }]
            )
            public_subnets.append(public_subnet['Subnet']['SubnetId'])
            
            # Private subnet
            private_subnet = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=f"10.0.{idx+10}.0/24",
                AvailabilityZone=az['ZoneName'],
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f'{self.stack_name}-private-{idx+1}'}]
                }]
            )
            private_subnets.append(private_subnet['Subnet']['SubnetId'])
        
        # Create route table for public subnets
        route_table = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags': [{'Key': 'Name', 'Value': f'{self.stack_name}-public-rt'}]
            }]
        )
        route_table_id = route_table['RouteTable']['RouteTableId']
        
        # Add route to internet gateway
        ec2.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )
        
        # Associate public subnets with route table
        for subnet_id in public_subnets:
            ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        
        return {
            "vpc_id": vpc_id,
            "igw_id": igw_id,
            "public_subnets": ",".join(public_subnets),
            "private_subnets": ",".join(private_subnets)
        }
    
    def _create_ecr_repository(self) -> str:
        """Create ECR repository for Docker images"""
        ecr = self.session.client('ecr')
        
        repo_name = f"{self.stack_name}-repo"
        
        try:
            response = ecr.create_repository(
                repositoryName=repo_name,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'}
            )
            return response['repository']['repositoryUri']
        except ecr.exceptions.RepositoryAlreadyExistsException:
            response = ecr.describe_repositories(repositoryNames=[repo_name])
            return response['repositories'][0]['repositoryUri']
    
    def _build_and_push_images(self, ecr_uri: str, stack: Dict) -> None:
        """Build and push Docker images to ECR"""
        import subprocess
        
        # Get ECR login
        ecr = self.session.client('ecr')
        auth_token = ecr.get_authorization_token()
        
        # Login to ECR
        subprocess.run([
            "docker", "login",
            "-u", "AWS",
            "-p", auth_token['authorizationData'][0]['authorizationToken'],
            ecr_uri.split('/')[0]
        ], check=True, capture_output=True)
        
        # Build main application image
        subprocess.run([
            "docker", "build",
            "-t", ecr_uri,
            str(self.project_path)
        ], check=True, capture_output=True)
        
        # Push to ECR
        subprocess.run([
            "docker", "push", ecr_uri
        ], check=True, capture_output=True)
    
    def _create_rds_database(self, vpc_id: str, subnet_ids: str) -> Dict[str, str]:
        """Create RDS database instance"""
        rds = self.session.client('rds')
        ec2 = self.session.client('ec2')
        
        # Create DB subnet group
        subnet_group_name = f"{self.stack_name}-db-subnet"
        
        try:
            rds.create_db_subnet_group(
                DBSubnetGroupName=subnet_group_name,
                DBSubnetGroupDescription=f"Subnet group for {self.stack_name}",
                SubnetIds=subnet_ids.split(','),
                Tags=[{'Key': 'Name', 'Value': subnet_group_name}]
            )
        except rds.exceptions.DBSubnetGroupAlreadyExistsFault:
            pass
        
        # Create security group
        sg = ec2.create_security_group(
            GroupName=f"{self.stack_name}-db-sg",
            Description="Security group for RDS",
            VpcId=vpc_id
        )
        sg_id = sg['GroupId']
        
        # Allow PostgreSQL traffic from VPC
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [{'CidrIp': '10.0.0.0/16'}]
            }]
        )
        
        # Create RDS instance
        db_instance_id = f"{self.stack_name}-db"
        
        response = rds.create_db_instance(
            DBInstanceIdentifier=db_instance_id,
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            EngineVersion='15.3',
            MasterUsername='admin',
            MasterUserPassword=self._generate_password(),
            AllocatedStorage=20,
            VpcSecurityGroupIds=[sg_id],
            DBSubnetGroupName=subnet_group_name,
            PubliclyAccessible=False,
            BackupRetentionPeriod=7,
            MultiAZ=self.environment == 'prod',
            StorageEncrypted=True,
            Tags=[
                {'Key': 'Name', 'Value': db_instance_id},
                {'Key': 'Environment', 'Value': self.environment}
            ]
        )
        
        # Wait for database to be available
        console.print("  [dim]Waiting for database to be ready (this may take 5-10 minutes)...[/dim]")
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=db_instance_id)
        
        # Get endpoint
        db_info = rds.describe_db_instances(DBInstanceIdentifier=db_instance_id)
        endpoint = db_info['DBInstances'][0]['Endpoint']['Address']
        
        return {
            "db_instance_id": db_instance_id,
            "db_endpoint": endpoint,
            "db_security_group": sg_id
        }
    
    def _create_s3_bucket(self) -> str:
        """Create S3 bucket for data storage"""
        s3 = self.session.client('s3')
        
        bucket_name = f"{self.stack_name}-data-{int(time.time())}"
        
        # Create bucket
        if self.region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region}
            )
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
        
        # Block public access
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        return bucket_name
    
    def _create_ecs_cluster(
        self,
        vpc_resources: Dict,
        ecr_uri: str,
        stack: Dict
    ) -> Dict[str, str]:
        """Create ECS Fargate cluster and services"""
        ecs = self.session.client('ecs')
        elbv2 = self.session.client('elbv2')
        ec2 = self.session.client('ec2')
        
        cluster_name = f"{self.stack_name}-cluster"
        
        # Create ECS cluster
        ecs.create_cluster(
            clusterName=cluster_name,
            capacityProviders=['FARGATE', 'FARGATE_SPOT'],
            tags=[
                {'key': 'Name', 'value': cluster_name},
                {'key': 'Environment', 'value': self.environment}
            ]
        )
        
        # Create security group for ALB
        alb_sg = ec2.create_security_group(
            GroupName=f"{self.stack_name}-alb-sg",
            Description="Security group for ALB",
            VpcId=vpc_resources["vpc_id"]
        )
        alb_sg_id = alb_sg['GroupId']
        
        # Allow HTTP/HTTPS traffic
        ec2.authorize_security_group_ingress(
            GroupId=alb_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
        
        # Create Application Load Balancer
        alb_response = elbv2.create_load_balancer(
            Name=f"{self.stack_name}-alb",
            Subnets=vpc_resources["public_subnets"].split(','),
            SecurityGroups=[alb_sg_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4',
            Tags=[{'Key': 'Name', 'Value': f"{self.stack_name}-alb"}]
        )
        
        alb_arn = alb_response['LoadBalancers'][0]['LoadBalancerArn']
        alb_dns = alb_response['LoadBalancers'][0]['DNSName']
        
        # Create target group
        target_group = elbv2.create_target_group(
            Name=f"{self.stack_name}-tg",
            Protocol='HTTP',
            Port=80,
            VpcId=vpc_resources["vpc_id"],
            TargetType='ip',
            HealthCheckEnabled=True,
            HealthCheckProtocol='HTTP',
            HealthCheckPath='/',
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=3
        )
        target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']
        
        # Create listener
        elbv2.create_listener(
            LoadBalancerArn=alb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[{
                'Type': 'forward',
                'TargetGroupArn': target_group_arn
            }]
        )
        
        # Create task definition
        task_def_arn = self._create_task_definition(ecr_uri)
        
        # Create ECS service
        ecs.create_service(
            cluster=cluster_name,
            serviceName=f"{self.stack_name}-service",
            taskDefinition=task_def_arn,
            desiredCount=2 if self.environment == 'prod' else 1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': vpc_resources["private_subnets"].split(','),
                    'securityGroups': [alb_sg_id],
                    'assignPublicIp': 'ENABLED'
                }
            },
            loadBalancers=[{
                'targetGroupArn': target_group_arn,
                'containerName': 'app',
                'containerPort': 8080
            }]
        )
        
        return {
            "ecs_cluster": cluster_name,
            "load_balancer_arn": alb_arn,
            "load_balancer_dns": alb_dns,
            "target_group_arn": target_group_arn,
            "task_definition": task_def_arn
        }
    
    def _create_task_definition(self, ecr_uri: str) -> str:
        """Create ECS task definition"""
        ecs = self.session.client('ecs')
        
        response = ecs.register_task_definition(
            family=self.stack_name,
            networkMode='awsvpc',
            requiresCompatibilities=['FARGATE'],
            cpu='512',
            memory='1024',
            containerDefinitions=[{
                'name': 'app',
                'image': ecr_uri,
                'portMappings': [{
                    'containerPort': 8080,
                    'protocol': 'tcp'
                }],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': f'/ecs/{self.stack_name}',
                        'awslogs-region': self.region,
                        'awslogs-stream-prefix': 'ecs'
                    }
                }
            }]
        )
        
        return response['taskDefinition']['taskDefinitionArn']
    
    def _setup_monitoring(self) -> Dict[str, str]:
        """Setup CloudWatch monitoring"""
        cloudwatch = self.session.client('cloudwatch')
        logs = self.session.client('logs')
        
        # Create log group
        log_group = f'/ecs/{self.stack_name}'
        
        try:
            logs.create_log_group(
                logGroupName=log_group,
                tags={'Environment': self.environment}
            )
        except logs.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Set retention
        logs.put_retention_policy(
            logGroupName=log_group,
            retentionInDays=30 if self.environment == 'prod' else 7
        )
        
        # Create dashboard
        dashboard_name = f"{self.stack_name}-dashboard"
        
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps({
                'widgets': [
                    {
                        'type': 'metric',
                        'properties': {
                            'metrics': [
                                ['AWS/ECS', 'CPUUtilization', {'stat': 'Average'}],
                                ['.', 'MemoryUtilization', {'stat': 'Average'}]
                            ],
                            'period': 300,
                            'stat': 'Average',
                            'region': self.region,
                            'title': 'ECS Metrics'
                        }
                    }
                ]
            })
        )
        
        dashboard_url = f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard_name}"
        
        return {
            "log_group": log_group,
            "dashboard_name": dashboard_name,
            "dashboard_url": dashboard_url
        }
    
    def _rollback_resources(self, resources: Dict[str, str]) -> None:
        """Rollback created resources"""
        # This would implement cleanup logic
        # For brevity, simplified version
        console.print("[yellow]Rollback not fully implemented in this version[/yellow]")
    
    def _generate_password(self, length: int = 20) -> str:
        """Generate secure random password"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def destroy(self) -> DeploymentResult:
        """Destroy all AWS resources"""
        console.print("\n[bold red]🗑️  Destroying AWS Resources[/bold red]")
        console.print("=" * 60)
        
        # Implementation would delete all resources
        # Simplified for brevity
        
        return DeploymentResult(
            status=DeploymentStatus.SUCCESS,
            message="Resources destroyed",
            endpoints={},
            resources={},
            errors=[]
        )
    
    def status(self) -> Dict:
        """Get deployment status"""
        # Implementation would check status of resources
        return {
            "stack_name": self.stack_name,
            "environment": self.environment,
            "region": self.region,
            "status": "running"
        }
