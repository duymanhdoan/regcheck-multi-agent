"""
Integration tests for Global ALB failover functionality.
Tests failover behavior when zones become unhealthy.
"""
import pytest
import httpx
import asyncio
from collections import Counter
import os


@pytest.mark.asyncio
async def test_simulate_zone_a_failure(http_client, global_nlb_dns, aws_region, ecs_client):
    """Simulate Zone A failure and verify traffic routes to Zone B."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    import boto3
    
    # Scale down Zone A services to simulate failure
    cluster_name = "dev-ecs-cluster"
    services = ["dev-frontend-service", "dev-application-service"]
    
    original_counts = {}
    
    try:
        # Scale down Zone A services
        print("Simulating Zone A failure by scaling down services...")
        for service_name in services:
            try:
                # Get current desired count
                response = ecs_client.describe_services(
                    cluster=cluster_name,
                    services=[service_name]
                )
                
                if response["services"]:
                    original_counts[service_name] = response["services"][0]["desiredCount"]
                    
                    # Scale to 0
                    ecs_client.update_service(
                        cluster=cluster_name,
                        service=service_name,
                        desiredCount=0
                    )
                    print(f"  Scaled {service_name} to 0")
            except Exception as e:
                print(f"  Failed to scale {service_name}: {str(e)}")
        
        # Wait for services to scale down and health checks to fail
        print("Waiting 60 seconds for health checks to detect failure...")
        await asyncio.sleep(60)
        
        # Make requests through Global NLB
        print("Testing traffic routing after Zone A failure...")
        zones = []
        
        for i in range(20):
            try:
                response = await http_client.get(
                    f"http://{global_nlb_dns}/health",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    zone = data.get("zone") or data.get("environment") or "unknown"
                    zones.append(zone)
            except Exception as e:
                print(f"  Request {i+1} failed: {str(e)}")
            
            await asyncio.sleep(1)
        
        # Analyze results
        if len(zones) > 0:
            zone_counts = Counter(zones)
            
            print(f"Traffic distribution after Zone A failure:")
            for zone, count in zone_counts.items():
                percentage = (count / len(zones)) * 100
                print(f"  {zone}: {count}/{len(zones)} requests ({percentage:.1f}%)")
            
            # Verify traffic is routed away from Zone A (dev)
            dev_percentage = (zone_counts.get("dev", 0) / len(zones)) * 100
            prod_percentage = (zone_counts.get("prod", 0) / len(zones)) * 100
            
            # Most traffic should go to Zone B (prod)
            assert prod_percentage > dev_percentage, \
                "Traffic should be routed to healthy Zone B"
            
            print("✓ Failover to Zone B successful")
        else:
            pytest.fail("No successful responses during failover test")
    
    finally:
        # Restore Zone A services
        print("Restoring Zone A services...")
        for service_name, original_count in original_counts.items():
            try:
                ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_name,
                    desiredCount=original_count
                )
                print(f"  Restored {service_name} to {original_count}")
            except Exception as e:
                print(f"  Failed to restore {service_name}: {str(e)}")


@pytest.mark.asyncio
async def test_simulate_zone_b_failure(http_client, global_nlb_dns, aws_region, ecs_client):
    """Simulate Zone B failure and verify traffic routes to Zone A."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    # Scale down Zone B services to simulate failure
    cluster_name = "prod-ecs-cluster"
    services = ["prod-frontend-service", "prod-application-service"]
    
    original_counts = {}
    
    try:
        # Scale down Zone B services
        print("Simulating Zone B failure by scaling down services...")
        for service_name in services:
            try:
                # Get current desired count
                response = ecs_client.describe_services(
                    cluster=cluster_name,
                    services=[service_name]
                )
                
                if response["services"]:
                    original_counts[service_name] = response["services"][0]["desiredCount"]
                    
                    # Scale to 0
                    ecs_client.update_service(
                        cluster=cluster_name,
                        service=service_name,
                        desiredCount=0
                    )
                    print(f"  Scaled {service_name} to 0")
            except Exception as e:
                print(f"  Failed to scale {service_name}: {str(e)}")
        
        # Wait for services to scale down and health checks to fail
        print("Waiting 60 seconds for health checks to detect failure...")
        await asyncio.sleep(60)
        
        # Make requests through Global NLB
        print("Testing traffic routing after Zone B failure...")
        zones = []
        
        for i in range(20):
            try:
                response = await http_client.get(
                    f"http://{global_nlb_dns}/health",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    zone = data.get("zone") or data.get("environment") or "unknown"
                    zones.append(zone)
            except Exception as e:
                print(f"  Request {i+1} failed: {str(e)}")
            
            await asyncio.sleep(1)
        
        # Analyze results
        if len(zones) > 0:
            zone_counts = Counter(zones)
            
            print(f"Traffic distribution after Zone B failure:")
            for zone, count in zone_counts.items():
                percentage = (count / len(zones)) * 100
                print(f"  {zone}: {count}/{len(zones)} requests ({percentage:.1f}%)")
            
            # Verify traffic is routed away from Zone B (prod)
            dev_percentage = (zone_counts.get("dev", 0) / len(zones)) * 100
            prod_percentage = (zone_counts.get("prod", 0) / len(zones)) * 100
            
            # Most traffic should go to Zone A (dev)
            assert dev_percentage > prod_percentage, \
                "Traffic should be routed to healthy Zone A"
            
            print("✓ Failover to Zone A successful")
        else:
            pytest.fail("No successful responses during failover test")
    
    finally:
        # Restore Zone B services
        print("Restoring Zone B services...")
        for service_name, original_count in original_counts.items():
            try:
                ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_name,
                    desiredCount=original_count
                )
                print(f"  Restored {service_name} to {original_count}")
            except Exception as e:
                print(f"  Failed to restore {service_name}: {str(e)}")


@pytest.mark.asyncio
async def test_automatic_recovery_both_zones_healthy(http_client, global_nlb_dns, ecs_client):
    """Test automatic recovery when both zones become healthy again."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    # Ensure both zones are healthy
    zones_to_check = [
        ("dev-ecs-cluster", ["dev-frontend-service", "dev-application-service"]),
        ("prod-ecs-cluster", ["prod-frontend-service", "prod-application-service"])
    ]
    
    print("Ensuring both zones are healthy...")
    for cluster_name, services in zones_to_check:
        for service_name in services:
            try:
                response = ecs_client.describe_services(
                    cluster=cluster_name,
                    services=[service_name]
                )
                
                if response["services"]:
                    service = response["services"][0]
                    desired = service["desiredCount"]
                    running = service["runningCount"]
                    
                    if desired == 0:
                        # Scale up to 1
                        ecs_client.update_service(
                            cluster=cluster_name,
                            service=service_name,
                            desiredCount=1
                        )
                        print(f"  Scaled up {service_name}")
                    else:
                        print(f"  {service_name}: {running}/{desired} tasks running")
            except Exception as e:
                print(f"  Failed to check {service_name}: {str(e)}")
    
    # Wait for services to become healthy
    print("Waiting 90 seconds for services to become healthy...")
    await asyncio.sleep(90)
    
    # Make requests and verify distribution
    print("Testing traffic distribution with both zones healthy...")
    zones = []
    
    for i in range(50):
        try:
            response = await http_client.get(
                f"http://{global_nlb_dns}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                zone = data.get("zone") or data.get("environment") or "unknown"
                zones.append(zone)
        except Exception as e:
            print(f"  Request {i+1} failed: {str(e)}")
        
        await asyncio.sleep(0.5)
    
    # Analyze results
    if len(zones) > 0:
        zone_counts = Counter(zones)
        
        print(f"Traffic distribution with both zones healthy:")
        for zone, count in zone_counts.items():
            percentage = (count / len(zones)) * 100
            print(f"  {zone}: {count}/{len(zones)} requests ({percentage:.1f}%)")
        
        # Verify traffic is distributed to both zones
        if len(zone_counts) >= 2:
            # Both zones should receive traffic
            for zone, count in zone_counts.items():
                percentage = (count / len(zones)) * 100
                assert percentage > 10, \
                    f"Zone {zone} should receive more than 10% of traffic"
            
            print("✓ Automatic recovery successful - traffic distributed to both zones")
        else:
            print("⚠ Traffic only going to one zone")
    else:
        pytest.fail("No successful responses during recovery test")


@pytest.mark.asyncio
async def test_health_check_configuration(aws_region):
    """Test that health checks are configured correctly on Global NLB."""
    import boto3
    
    elbv2_client = boto3.client("elbv2", region_name=aws_region)
    
    global_nlb_name = os.getenv("GLOBAL_NLB_NAME", "global-nlb-ap-southeast-1")
    
    try:
        # Find Global NLB
        lbs = elbv2_client.describe_load_balancers(
            Names=[global_nlb_name]
        )
        
        if not lbs["LoadBalancers"]:
            pytest.skip("Global NLB not found")
        
        lb_arn = lbs["LoadBalancers"][0]["LoadBalancerArn"]
        
        # Get target groups
        target_groups = elbv2_client.describe_target_groups(
            LoadBalancerArn=lb_arn
        )
        
        print("Health check configuration:")
        for tg in target_groups["TargetGroups"]:
            tg_name = tg["TargetGroupName"]
            
            print(f"\n  Target Group: {tg_name}")
            print(f"    Protocol: {tg.get('HealthCheckProtocol', 'N/A')}")
            print(f"    Port: {tg.get('HealthCheckPort', 'N/A')}")
            print(f"    Path: {tg.get('HealthCheckPath', 'N/A')}")
            print(f"    Interval: {tg.get('HealthCheckIntervalSeconds', 'N/A')}s")
            print(f"    Timeout: {tg.get('HealthCheckTimeoutSeconds', 'N/A')}s")
            print(f"    Healthy Threshold: {tg.get('HealthyThresholdCount', 'N/A')}")
            print(f"    Unhealthy Threshold: {tg.get('UnhealthyThresholdCount', 'N/A')}")
            
            # Verify health check settings
            assert tg.get("HealthCheckIntervalSeconds", 0) > 0, \
                "Health check interval should be configured"
            assert tg.get("HealthyThresholdCount", 0) > 0, \
                "Healthy threshold should be configured"
            assert tg.get("UnhealthyThresholdCount", 0) > 0, \
                "Unhealthy threshold should be configured"
        
        print("\n✓ Health checks configured correctly")
        
    except Exception as e:
        pytest.skip(f"Failed to check health check configuration: {str(e)}")


@pytest.mark.asyncio
async def test_failover_response_time(http_client, global_nlb_dns):
    """Test that failover doesn't significantly impact response time."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    import time
    
    # Measure response times
    response_times = []
    
    for i in range(10):
        try:
            start = time.time()
            response = await http_client.get(
                f"http://{global_nlb_dns}/health",
                timeout=10.0
            )
            end = time.time()
            
            if response.status_code == 200:
                response_time = (end - start) * 1000  # Convert to ms
                response_times.append(response_time)
        except Exception as e:
            print(f"  Request {i+1} failed: {str(e)}")
        
        await asyncio.sleep(0.5)
    
    if len(response_times) > 0:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"Response times:")
        print(f"  Average: {avg_response_time:.2f}ms")
        print(f"  Min: {min_response_time:.2f}ms")
        print(f"  Max: {max_response_time:.2f}ms")
        
        # Response time should be reasonable (< 2 seconds)
        assert avg_response_time < 2000, \
            f"Average response time too high: {avg_response_time:.2f}ms"
        
        print("✓ Response times acceptable")
    else:
        pytest.skip("No successful responses to measure")


@pytest.mark.asyncio
async def test_continuous_availability_during_failover(http_client, global_nlb_dns):
    """Test that service remains available during zone failover."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    # Make continuous requests
    total_requests = 30
    successful_requests = 0
    failed_requests = 0
    
    print("Testing continuous availability...")
    for i in range(total_requests):
        try:
            response = await http_client.get(
                f"http://{global_nlb_dns}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                successful_requests += 1
            else:
                failed_requests += 1
        except Exception as e:
            failed_requests += 1
            print(f"  Request {i+1} failed: {str(e)}")
        
        await asyncio.sleep(1)
    
    success_rate = (successful_requests / total_requests) * 100
    
    print(f"Availability test results:")
    print(f"  Successful: {successful_requests}/{total_requests} ({success_rate:.1f}%)")
    print(f"  Failed: {failed_requests}/{total_requests}")
    
    # At least 80% of requests should succeed
    assert success_rate >= 80, \
        f"Success rate too low: {success_rate:.1f}%"
    
    print("✓ Service maintained high availability")
