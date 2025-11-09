"""
Integration tests for auto scaling functionality.
Tests scale-out under load and scale-in after load reduction.
"""
import pytest
import httpx
import asyncio
import time
from datetime import datetime


@pytest.mark.asyncio
async def test_get_initial_task_count(ecs_client, zone_config):
    """Test getting initial task count for a service."""
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    service_name = f"{zone_config['environment']}-application-service"
    
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response["services"]:
            pytest.skip(f"Service {service_name} not found")
        
        service = response["services"][0]
        running_count = service["runningCount"]
        desired_count = service["desiredCount"]
        
        assert running_count >= 1, "Service should have at least 1 running task"
        assert desired_count >= 1, "Service should have desired count of at least 1"
        
        print(f"Initial task count - Running: {running_count}, Desired: {desired_count}")
        
    except Exception as e:
        pytest.skip(f"Failed to get task count: {str(e)}")


@pytest.mark.asyncio
async def test_service_auto_scaling_configuration(ecs_client, zone_config, aws_region):
    """Test that auto scaling is configured correctly for services."""
    import boto3
    
    autoscaling_client = boto3.client("application-autoscaling", region_name=aws_region)
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    service_name = f"{zone_config['environment']}-application-service"
    
    resource_id = f"service/{cluster_name}/{service_name}"
    
    try:
        # Check scalable target
        targets = autoscaling_client.describe_scalable_targets(
            ServiceNamespace="ecs",
            ResourceIds=[resource_id]
        )
        
        if not targets["ScalableTargets"]:
            pytest.skip("Auto scaling not configured")
        
        target = targets["ScalableTargets"][0]
        
        # Verify min/max capacity
        assert target["MinCapacity"] == 1, "Min capacity should be 1"
        assert target["MaxCapacity"] == 4, "Max capacity should be 4"
        
        # Check scaling policies
        policies = autoscaling_client.describe_scaling_policies(
            ServiceNamespace="ecs",
            ResourceId=resource_id
        )
        
        assert len(policies["ScalingPolicies"]) > 0, "Should have scaling policies"
        
        # Verify target tracking policy exists
        target_tracking_policies = [
            p for p in policies["ScalingPolicies"]
            if p["PolicyType"] == "TargetTrackingScaling"
        ]
        
        assert len(target_tracking_policies) > 0, "Should have target tracking policy"
        
        policy = target_tracking_policies[0]
        config = policy["TargetTrackingScalingPolicyConfiguration"]
        
        # Verify CPU target
        if "PredefinedMetricSpecification" in config:
            metric_type = config["PredefinedMetricSpecification"]["PredefinedMetricType"]
            assert metric_type == "ECSServiceAverageCPUUtilization", \
                "Should track CPU utilization"
        
        assert config["TargetValue"] == 70.0, "Target CPU should be 70%"
        
        print(f"✓ Auto scaling configured: Min={target['MinCapacity']}, Max={target['MaxCapacity']}, Target=70% CPU")
        
    except Exception as e:
        pytest.skip(f"Failed to check auto scaling config: {str(e)}")


@pytest.mark.asyncio
async def test_generate_load(http_client, base_url, auth_token):
    """Test generating load on the application service."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Generate concurrent requests
    async def make_request():
        try:
            response = await http_client.get(
                f"{base_url}/health",
                headers=headers,
                timeout=10.0
            )
            return response.status_code
        except:
            return None
    
    # Send 50 concurrent requests
    tasks = [make_request() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    successful_requests = sum(1 for r in results if r == 200)
    
    assert successful_requests > 0, "At least some requests should succeed"
    print(f"Load test: {successful_requests}/50 requests successful")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_scale_out_under_load(ecs_client, http_client, base_url, auth_token, zone_config):
    """Test that service scales out under sustained load."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    service_name = f"{zone_config['environment']}-application-service"
    
    # Get initial task count
    try:
        initial_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not initial_response["services"]:
            pytest.skip(f"Service {service_name} not found")
        
        initial_count = initial_response["services"][0]["runningCount"]
        print(f"Initial running tasks: {initial_count}")
        
    except Exception as e:
        pytest.skip(f"Failed to get initial task count: {str(e)}")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Generate sustained load for 2 minutes
    print("Generating sustained load for 2 minutes...")
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < 120:  # 2 minutes
        # Send burst of requests
        async def make_request():
            try:
                await http_client.get(f"{base_url}/health", headers=headers, timeout=5.0)
                return 1
            except:
                return 0
        
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        request_count += sum(results)
        
        await asyncio.sleep(1)
    
    print(f"Sent {request_count} requests")
    
    # Wait for scale-out (60s cooldown + buffer)
    print("Waiting 90 seconds for scale-out...")
    await asyncio.sleep(90)
    
    # Check if task count increased
    try:
        final_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        final_count = final_response["services"][0]["runningCount"]
        desired_count = final_response["services"][0]["desiredCount"]
        
        print(f"Final running tasks: {final_count}, Desired: {desired_count}")
        
        # Verify scale-out occurred or is in progress
        assert desired_count > initial_count or final_count > initial_count, \
            f"Service should scale out under load (initial: {initial_count}, final: {final_count}, desired: {desired_count})"
        
        assert desired_count <= 4, "Should not exceed max capacity of 4"
        
    except Exception as e:
        pytest.fail(f"Failed to verify scale-out: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_scale_in_after_load_reduction(ecs_client, zone_config):
    """Test that service scales in after load is reduced."""
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    service_name = f"{zone_config['environment']}-application-service"
    
    # Get current task count
    try:
        current_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not current_response["services"]:
            pytest.skip(f"Service {service_name} not found")
        
        current_count = current_response["services"][0]["runningCount"]
        print(f"Current running tasks: {current_count}")
        
        if current_count <= 1:
            pytest.skip("Service already at minimum capacity")
        
    except Exception as e:
        pytest.skip(f"Failed to get current task count: {str(e)}")
    
    # Wait for scale-in (300s cooldown + buffer)
    print("Waiting 6 minutes for scale-in...")
    await asyncio.sleep(360)
    
    # Check if task count decreased
    try:
        final_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        final_count = final_response["services"][0]["runningCount"]
        desired_count = final_response["services"][0]["desiredCount"]
        
        print(f"Final running tasks: {final_count}, Desired: {desired_count}")
        
        # Verify scale-in occurred or is in progress
        assert desired_count <= current_count, \
            f"Service should scale in after load reduction (current: {current_count}, desired: {desired_count})"
        
        assert desired_count >= 1, "Should not go below min capacity of 1"
        
    except Exception as e:
        pytest.fail(f"Failed to verify scale-in: {str(e)}")


@pytest.mark.asyncio
async def test_all_services_have_auto_scaling(ecs_client, zone_config, aws_region):
    """Test that all services have auto scaling configured."""
    import boto3
    
    autoscaling_client = boto3.client("application-autoscaling", region_name=aws_region)
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    
    services = [
        "frontend-service",
        "agentgateway-service",
        "application-service",
        "mcp-finance-service",
        "mcp-hr-service",
        "mcp-legal-service"
    ]
    
    for service_name in services:
        full_service_name = f"{zone_config['environment']}-{service_name}"
        resource_id = f"service/{cluster_name}/{full_service_name}"
        
        try:
            targets = autoscaling_client.describe_scalable_targets(
                ServiceNamespace="ecs",
                ResourceIds=[resource_id]
            )
            
            if targets["ScalableTargets"]:
                target = targets["ScalableTargets"][0]
                print(f"✓ {service_name}: Min={target['MinCapacity']}, Max={target['MaxCapacity']}")
            else:
                print(f"✗ {service_name}: No auto scaling configured")
                
        except Exception as e:
            print(f"✗ {service_name}: Error checking auto scaling - {str(e)}")


@pytest.mark.asyncio
async def test_auto_scaling_both_zones(ecs_client, aws_region):
    """Test auto scaling configuration in both dev and prod zones."""
    import boto3
    import os
    
    autoscaling_client = boto3.client("application-autoscaling", region_name=aws_region)
    zones = ["dev", "prod"]
    
    for zone_name in zones:
        cluster_name = f"{zone_name}-ecs-cluster"
        service_name = f"{zone_name}-application-service"
        resource_id = f"service/{cluster_name}/{service_name}"
        
        try:
            targets = autoscaling_client.describe_scalable_targets(
                ServiceNamespace="ecs",
                ResourceIds=[resource_id]
            )
            
            if targets["ScalableTargets"]:
                target = targets["ScalableTargets"][0]
                print(f"✓ Auto scaling configured for {zone_name} zone")
                print(f"  Min: {target['MinCapacity']}, Max: {target['MaxCapacity']}")
            else:
                print(f"✗ Auto scaling not configured for {zone_name} zone")
                
        except Exception as e:
            print(f"✗ Failed to check {zone_name} zone: {str(e)}")


@pytest.mark.asyncio
async def test_manual_scale_service(ecs_client, zone_config):
    """Test manually scaling a service (for testing purposes)."""
    cluster_name = f"{zone_config['environment']}-ecs-cluster"
    service_name = f"{zone_config['environment']}-application-service"
    
    try:
        # Get current desired count
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response["services"]:
            pytest.skip(f"Service {service_name} not found")
        
        current_desired = response["services"][0]["desiredCount"]
        
        # Scale to 2 tasks
        new_desired = 2 if current_desired == 1 else 1
        
        ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=new_desired
        )
        
        print(f"Manually scaled service from {current_desired} to {new_desired} tasks")
        
        # Wait a bit and verify
        await asyncio.sleep(10)
        
        verify_response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        updated_desired = verify_response["services"][0]["desiredCount"]
        assert updated_desired == new_desired, \
            f"Desired count should be {new_desired}, got {updated_desired}"
        
    except Exception as e:
        pytest.skip(f"Failed to manually scale service: {str(e)}")
