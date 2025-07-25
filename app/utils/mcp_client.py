"""
MCP Client for connecting to MCP Atlassian server
This module provides a proper MCP client interface for the Streamlit dashboard
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
import streamlit as st

logger = logging.getLogger(__name__)

class MCPAtlassianClient:
    """
    MCP client for connecting to the Atlassian MCP server
    """
    
    def __init__(self, server_url: str = "http://localhost:3000/mcp/"):
        self.server_url = server_url
        self.client = None
        self.session_id = None
    
    def _parse_sse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Server-Sent Events response format
        """
        try:
            # Handle SSE format: "event: message\ndata: {json}"
            if "event: message" in response_text and "data: " in response_text:
                # Extract JSON from SSE format
                lines = response_text.strip().split('\n')
                for line in lines:
                    if line.startswith("data: "):
                        json_data = line[6:]  # Remove "data: " prefix
                        return json.loads(json_data)
            
            # Try parsing as regular JSON
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response_text[:200]}...")
            raise e
    
    async def _send_initialized_notification(self):
        """
        Send the initialized notification to complete the MCP handshake
        """
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            if self.session_id:
                headers["mcp-session-id"] = self.session_id
            
            # Send notification (no response expected)
            await self.client.post(
                self.server_url,
                json=notification,
                headers=headers
            )
            
            logger.info("Sent initialized notification to MCP server")
            
        except Exception as e:
            logger.error(f"Error sending initialized notification: {str(e)}")
        
    async def connect(self) -> bool:
        """
        Connect to the MCP server
        """
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Initialize MCP session
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "pi-planning-dashboard",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self.client.post(
                self.server_url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                # Handle SSE response format
                result = self._parse_sse_response(response.text)
                if "result" in result:
                    # Extract session ID from headers
                    self.session_id = response.headers.get('mcp-session-id')
                    logger.info(f"Successfully connected to MCP Atlassian server with session ID: {self.session_id}")
                    
                    # Send initialized notification
                    await self._send_initialized_notification()
                    return True
            
            logger.error(f"Failed to connect to MCP server: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {str(e)}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            if self.session_id:
                headers["mcp-session-id"] = self.session_id
            
            response = await self.client.post(
                self.server_url,
                json=request,
                headers=headers
            )
            
            if response.status_code == 200:
                result = self._parse_sse_response(response.text)
                if "result" in result and "tools" in result["result"]:
                    return result["result"]["tools"]
            
            logger.error(f"Failed to list tools: {response.status_code} - {response.text}")
            return []
            
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            if self.session_id:
                headers["mcp-session-id"] = self.session_id
            
            response = await self.client.post(
                self.server_url,
                json=request,
                headers=headers
            )
            
            if response.status_code == 200:
                result = self._parse_sse_response(response.text)
                if "result" in result:
                    return {
                        "success": True,
                        "result": result["result"],
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                elif "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
            
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "tool_name": tool_name,
                "arguments": arguments
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "arguments": arguments
            }
    
    async def disconnect(self):
        """
        Disconnect from the MCP server
        """
        if self.client:
            await self.client.aclose()
            self.client = None

# Synchronous wrapper for Streamlit
class StreamlitMCPClient:
    """
    Synchronous wrapper for the MCP client to work with Streamlit
    """
    
    def __init__(self, server_url: str = "http://localhost:3000/mcp/"):
        self.server_url = server_url
        self._client = None
    
    def _get_or_create_loop(self):
        """Get or create an event loop for async operations"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    
    def connect(self) -> bool:
        """Connect to the MCP server (synchronous)"""
        loop = self._get_or_create_loop()
        
        async def _connect():
            self._client = MCPAtlassianClient(self.server_url)
            return await self._client.connect()
        
        try:
            return loop.run_until_complete(_connect())
        except Exception as e:
            st.error(f"Failed to connect to MCP server: {str(e)}")
            return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools (synchronous)"""
        if not self._client:
            if not self.connect():
                return []
        
        loop = self._get_or_create_loop()
        
        try:
            return loop.run_until_complete(self._client.list_tools())
        except Exception as e:
            st.error(f"Failed to list tools: {str(e)}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool (synchronous)"""
        if not self._client:
            if not self.connect():
                return {
                    "success": False,
                    "error": "Failed to connect to MCP server",
                    "tool_name": tool_name,
                    "arguments": arguments
                }
        
        loop = self._get_or_create_loop()
        
        try:
            return loop.run_until_complete(self._client.call_tool(tool_name, arguments))
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "arguments": arguments
            }
    
    def disconnect(self):
        """Disconnect from the MCP server (synchronous)"""
        if self._client:
            loop = self._get_or_create_loop()
            try:
                loop.run_until_complete(self._client.disconnect())
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
            finally:
                self._client = None

# Global client instance for Streamlit
_mcp_client = None

def get_mcp_client() -> StreamlitMCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = StreamlitMCPClient()
    return _mcp_client

def test_mcp_connection() -> Dict[str, Any]:
    """
    Test the MCP connection and return status information
    """
    client = get_mcp_client()
    
    # Test connection
    connected = client.connect()
    if not connected:
        return {
            "connected": False,
            "error": "Failed to connect to MCP server",
            "tools": []
        }
    
    # Test listing tools
    tools = client.list_tools()
    
    return {
        "connected": True,
        "tools": tools,
        "tool_count": len(tools),
        "server_url": client.server_url
    }

def create_jira_issue_via_mcp(
    project: str,
    issue_type: str,
    summary: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a JIRA issue using the MCP Atlassian server
    """
    client = get_mcp_client()
    
    # Prepare arguments for jira_create_issue tool (using correct parameter names)
    arguments = {
        "project_key": project,
        "issue_type": issue_type,
        "summary": summary,
        "description": description
    }
    
    # Call the MCP tool
    result = client.call_tool("jira_create_issue", arguments)
    
    return result
