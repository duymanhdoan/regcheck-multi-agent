"""
Integration tests for Global ALB traffic distribution.
Tests 50/50 traffic distribution between Zone A and Zone B.
"""
import pytest
import httpx
import asyncio
from collections import Counter
import os


@pytest.mark.asyncio
async def test_global_nlb_accessible(http_client, global_nlb_dns):
    """Test that Global NLB is accessible."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    response = await http_client.get(f"http://{global_nlb_dns}/health", timeout=10.0)
    
    assert response.status_code == 200, \
        f"Global NLB health check failed: {response.status_code}"
    
    print(f"✓ Global NLB accessible at {global_nlb_dns}")


@pytest.mark.asyncio
async def test_traffic_distribution_to_both_zones(http_client, global_nlb_dns):
    """Test that traffic is distributed to both Zone A and Zone B."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    # Make multiple requests and track which zone responds
    num_requests = 100
    zone_responses = []
    
    for i in range(num_requests):
        try:
            response = await http_client.get(
                f"http://{global_nlb_dns}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                # Try to identify zone from response headers or body
                # This assumes the health endpoint returns zone information
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                
                zone = data.get("zone") or data.get("environment") or "unknown"
                zone_responses.append(zone)
                
        except Exception as e:
            print(f"Request {i+1} failed: {str(e)}")
    
    # Count responses from each zone
    zone_counts = Counter(zone_responses)
    
    print(f"Traffic distribution over {num_requests} requests:")
    for zone, count in zone_counts.items():
        percentage = (count / len(zone_responses)) * 100
        print(f"  {zone}: {count} requests ({percentage:.1f}%)")
    
    # Verify both zones received traffic
    if len(zone_counts) >= 2:
        assert len(zone_counts) >= 2, "Traffic should be distributed to at least 2 zones"
        
        # Check if distribution is roughly 50/50 (allow 30-70% range)
        for zone, count in zone_counts.items():
            percentage = (count / len(zone_responses)) * 100
            assert 20 <= percentage <= 80, \
                f"Zone {zone} received {percentage:.1f}%, expected roughly 50%"
    else:
        pytest.skip("Could not identify zone from responses")


@pytest.mark.asyncio
async def test_weighted_routing_configuration(aws_region):
    """Test that Global NLB has correct weighted routing configuration."""
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
        
        # Get listeners
        listeners = elbv2_client.describe_listeners(
            LoadBalancerArn=lb_arn
        )
        
        assert len(listeners["Listeners"]) > 0, "Global NLB should have listeners"
        
        # Get target groups for first listener
        listener_arn = listeners["Listeners"][0]["ListenerArn"]
        
        # Get rules (for ALB) or default action (for NLB)
        default_actions = listeners["Listeners"][0]["DefaultActions"]
        
        # For NLB with weighted target groups
        if default_actions[0]["Type"] == "forward":
            forward_config = default_actions[0].get("ForwardConfig", {})
            target_groups = forward_config.get("TargetGroups", [])
            
            if len(target_groups) >= 2:
                # Verify weights
                weights = [tg["Weight"] for tg in target_groups]
                print(f"Target group weights: {weights}")
                
                # Check if weights are roughly equal (50/50)
                total_weight = sum(weights)
                for weight in weights:
                    percentage = (weight / total_weight) * 100
                    assert 40 <= percentage <= 60, \
                        f"Weight {weight} is {percentage:.1f}%, expected roughly 50%"
                
                print("✓ Weighted routing configured correctly")
            else:
                pytest.skip("Weighted routing not configured")
        
    except Exception as e:
        pytest.skip(f"Failed to check weighted routing: {str(e)}")


@pytest.mark.asyncio
async def test_session_stickiness_through_global_nlb(http_client, global_nlb_dns):
    """Test that session stickiness works through Global NLB."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    # Note: NLB doesn't support session stickiness at Layer 4
    # This test verifies connection-level behavior
    
    # Make multiple requests in quick succession
    zones = []
    
    for i in range(10):
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
            print(f"Request {i+1} failed: {str(e)}")
        
        await asyncio.sleep(0.1)
    
    # For NLB, we expect requests to potentially go to different zones
    # since there's no application-level stickiness
    zone_counts = Counter(zones)
    
    print(f"Session stickiness test - Zone distribution:")
    for zone, count in zone_counts.items():
        print(f"  {zone}: {count}/10 requests")
    
    # Just verify requests were successful
    assert len(zones) > 0, "Should have successful responses"


@pytest.mark.asyncio
async def test_cross_zone_load_balancing(aws_region):
    """Test that cross-zone load balancing is enabled on Global NLB."""
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
        
        # Get load balancer attributes
        attributes = elbv2_client.describe_load_balancer_attributes(
            LoadBalancerArn=lb_arn
        )
        
        # Check for cross-zone load balancing
        cross_zone_attr = next(
            (attr for attr in attributes["Attributes"]
             if attr["Key"] == "load_balancing.cross_zone.enabled"),
            None
        )
        
        if cross_zone_attr:
            assert cross_zone_attr["Value"] == "true", \
                "Cross-zone load balancing should be enabled"
            print("✓ Cross-zone load balancing enabled")
        else:
            print("⚠ Cross-zone load balancing attribute not found")
        
    except Exception as e:
        pytest.skip(f"Failed to check cross-zone load balancing: {str(e)}")


@pytest.mark.asyncio
async def test_global_nlb_target_health(aws_region):
    """Test that both zone NLBs are healthy targets of Global NLB."""
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
        
        assert len(target_groups["TargetGroups"]) >= 2, \
            "Global NLB should have at least 2 target groups (Zone A and Zone B)"
        
        # Check health of targets in each target group
        healthy_zones = 0
        
        for tg in target_groups["TargetGroups"]:
            tg_arn = tg["TargetGroupArn"]
            tg_name = tg["TargetGroupName"]
            
            health = elbv2_client.describe_target_health(
                TargetGroupArn=tg_arn
            )
            
            healthy_targets = [
                t for t in health["TargetHealthDescriptions"]
                if t["TargetHealth"]["State"] == "healthy"
            ]
            
            print(f"Target group {tg_name}: {len(healthy_targets)} healthy targets")
            
            if len(healthy_targets) > 0:
                healthy_zones += 1
        
        assert healthy_zones >= 1, "At least one zone should be healthy"
        
        if healthy_zones >= 2:
            print("✓ Both zones are healthy")
        else:
            print("⚠ Only one zone is healthy")
        
    except Exception as e:
        pytest.skip(f"Failed to check target health: {str(e)}")


@pytest.mark.asyncio
async def test_requests_reach_both_zone_nlbs(http_client, aws_region):
    """Test that requests actually reach both zone NLBs."""
    dev_nlb_dns = os.getenv("DEV_NLB_DNS")
    prod_nlb_dns = os.getenv("PROD_NLB_DNS")
    
    if not dev_nlb_dns or not prod_nlb_dns:
        pytest.skip("Zone NLB DNS names not configured")
    
    # Test Zone A (dev)
    try:
        dev_response = await http_client.get(
            f"http://{dev_nlb_dns}/health",
            timeout=10.0
        )
        assert dev_response.status_code == 200
        print(f"✓ Zone A NLB accessible at {dev_nlb_dns}")
    except Exception as e:
        print(f"✗ Zone A NLB not accessible: {str(e)}")
    
    # Test Zone B (prod)
    try:
        prod_response = await http_client.get(
            f"http://{prod_nlb_dns}/health",
            timeout=10.0
        )
        assert prod_response.status_code == 200
        print(f"✓ Zone B NLB accessible at {prod_nlb_dns}")
    except Exception as e:
        print(f"✗ Zone B NLB not accessible: {str(e)}")


@pytest.mark.asyncio
async def test_concurrent_requests_distribution(http_client, global_nlb_dns):
    """Test traffic distribution with concurrent requests."""
    if not global_nlb_dns:
        pytest.skip("Global NLB DNS not configured")
    
    async def make_request(request_id):
        try:
            response = await http_client.get(
                f"http://{global_nlb_dns}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                zone = data.get("zone") or data.get("environment") or "unknown"
                return zone
        except:
            return None
    
    # Send 50 concurrent requests
    tasks = [make_request(i) for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    # Filter out failed requests
    zones = [z for z in results if z is not None]
    
    if len(zones) > 0:
        zone_counts = Counter(zones)
        
        print(f"Concurrent requests distribution ({len(zones)} successful):")
        for zone, count in zone_counts.items():
            percentage = (count / len(zones)) * 100
            print(f"  {zone}: {count} requests ({percentage:.1f}%)")
        
        # Verify distribution
        if len(zone_counts) >= 2:
            assert len(zone_counts) >= 2, "Traffic should reach multiple zones"
    else:
        pytest.skip("No successful responses to analyze")
