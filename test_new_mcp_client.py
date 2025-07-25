#!/usr/bin/env python3
"""
Test script for the new MCP client implementation
"""

import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from utils.mcp_client import test_mcp_connection, create_jira_issue_via_mcp, get_mcp_client

def main():
    print("🚀 Testing New MCP Client Implementation")
    print("=" * 50)
    
    # Test 1: Connection and tool listing
    print("\n📡 Testing MCP Connection...")
    connection_result = test_mcp_connection()
    
    if connection_result["connected"]:
        print(f"✅ Successfully connected to MCP server!")
        print(f"🔗 Server URL: {connection_result['server_url']}")
        print(f"🛠️  Available tools: {connection_result['tool_count']}")
        
        # List some tools
        tools = connection_result["tools"]
        if tools:
            print("\n📋 Available Tools:")
            for i, tool in enumerate(tools[:10]):  # Show first 10 tools
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                print(f"  {i+1}. {name}")
                print(f"     {description[:80]}{'...' if len(description) > 80 else ''}")
            
            if len(tools) > 10:
                print(f"     ... and {len(tools) - 10} more tools")
        
        # Test 2: Try creating a JIRA issue
        print(f"\n🎯 Testing JIRA Issue Creation...")
        
        # Look for jira_create_issue tool
        jira_tools = [t for t in tools if "jira" in t.get("name", "").lower()]
        create_tool = next((t for t in jira_tools if "create" in t.get("name", "").lower()), None)
        
        if create_tool:
            print(f"✅ Found JIRA creation tool: {create_tool['name']}")
            
            # Test creating an issue
            result = create_jira_issue_via_mcp(
                project="PD",
                issue_type="Epic",
                summary="Test Epic from PI Planning Dashboard",
                description="This is a test Epic created via the new MCP client integration"
            )
            
            if result["success"]:
                print("✅ Successfully created JIRA issue!")
                print(f"📋 Result: {result['result']}")
            else:
                print(f"❌ Failed to create JIRA issue: {result['error']}")
        else:
            print("⚠️  No JIRA creation tool found")
            print("Available JIRA tools:")
            for tool in jira_tools:
                print(f"  - {tool.get('name', 'Unknown')}")
    
    else:
        print(f"❌ Failed to connect to MCP server")
        print(f"Error: {connection_result.get('error', 'Unknown error')}")
        
        print("\n💡 Troubleshooting:")
        print("1. Make sure your MCP Atlassian server is running")
        print("2. Check that it's running on http://localhost:3000/mcp")
        print("3. Verify the server is using streamable-http transport")
    
    print(f"\n🏁 Test completed!")

if __name__ == "__main__":
    main()
