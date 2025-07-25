#!/usr/bin/env python3
"""
Test script to verify MCP Atlassian server connection
This script helps debug MCP server connectivity issues
"""

import requests
import json
import sys
from typing import Dict, Any

def test_mcp_connection():
    """Test connection to MCP Atlassian server"""
    
    # Possible MCP server URLs to try
    possible_urls = [
        "http://localhost:3000",
        "http://localhost:3000:3000", 
        "http://localhost:9000",
        "http://127.0.0.1:3000"
    ]
    
    # Try different endpoint paths
    endpoint_paths = ["/mcp", "/sse", "", "/api"]
    
    print("🔍 Testing MCP Atlassian Server Connection...")
    print("=" * 50)
    
    for base_url in possible_urls:
        print(f"\n📡 Testing base URL: {base_url}")
        
        for endpoint in endpoint_paths:
            full_url = f"{base_url.rstrip('/')}{endpoint}"
            print(f"  🔗 Trying: {full_url}")
            
            try:
                # Test 1: Basic connectivity
                response = requests.get(full_url, timeout=5)
                print(f"    ✅ GET request successful: {response.status_code}")
                
                # Test 2: MCP tools/list call
                mcp_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
                
                response = requests.post(
                    full_url,
                    json=mcp_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✅ MCP tools/list successful!")
                    print(f"    📋 Available tools: {len(result.get('result', {}).get('tools', []))}")
                    
                    # List available tools
                    tools = result.get('result', {}).get('tools', [])
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"      - {tool.get('name', 'Unknown')}")
                    
                    if len(tools) > 5:
                        print(f"      ... and {len(tools) - 5} more tools")
                    
                    print(f"\n🎉 SUCCESS! MCP server found at: {full_url}")
                    return full_url
                    
                else:
                    print(f"    ❌ MCP call failed: {response.status_code} - {response.text[:100]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"    ❌ Connection refused")
            except requests.exceptions.Timeout:
                print(f"    ❌ Request timed out")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
    
    print(f"\n❌ No working MCP server found!")
    print("\n💡 Troubleshooting Tips:")
    print("1. Make sure your MCP Atlassian server is running")
    print("2. Check the port number (common ports: 3000, 9000)")
    print("3. Verify the server is configured for HTTP transport")
    print("4. Check server logs for any startup errors")
    
    return None

def test_jira_create_issue(mcp_url: str):
    """Test creating a JIRA issue via MCP"""
    
    print(f"\n🎯 Testing JIRA issue creation at: {mcp_url}")
    print("=" * 50)
    
    # Test issue creation
    mcp_payload = {
        "method": "tools/call",
        "params": {
            "name": "jira_create_issue",
            "arguments": {
                "project": "PD",
                "issueType": "Epic",
                "summary": "Test Epic from PI Planning Dashboard",
                "description": "This is a test Epic created via MCP integration",
                "priority": "Medium"
            }
        }
    }
    
    try:
        response = requests.post(
            mcp_url,
            json=mcp_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ JIRA issue creation test successful!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ JIRA issue creation failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing JIRA issue creation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 MCP Atlassian Server Connection Test")
    print("=" * 50)
    
    # Test connection
    working_url = test_mcp_connection()
    
    if working_url:
        print(f"\n✅ Update your .env file with:")
        print(f"JIRA_MCP_SERVER_URL={working_url}")
        
        # Test JIRA functionality
        if "--test-jira" in sys.argv:
            test_jira_create_issue(working_url)
    else:
        print("\n📋 MCP Server Setup Instructions:")
        print("1. Install MCP Atlassian: docker pull ghcr.io/sooperset/mcp-atlassian:latest")
        print("2. Run with HTTP transport:")
        print("   docker run --rm -p 3000:3000 \\")
        print("     -e JIRA_URL=https://brandonblack.atlassian.net \\")
        print("     -e JIRA_USERNAME=bmblack+agent@gmail.com \\")
        print("     -e JIRA_API_TOKEN=your-token \\")
        print("     ghcr.io/sooperset/mcp-atlassian:latest \\")
        print("     --transport streamable-http --port 3000")
