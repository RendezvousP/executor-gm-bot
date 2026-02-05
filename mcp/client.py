"""
EXECUTOR - MCP Client
Connects to external MCP servers (Antigravity, OpenCode, etc.)
"""
import httpx
import logging
import json
from typing import Any, Optional

logger = logging.getLogger("EXECUTOR.MCP.Client")

class MCPClient:
    """Client to connect to external MCP servers."""
    
    def __init__(self, name: str, url: str, enabled: bool = False):
        self.name = name
        self.url = url
        self.enabled = enabled
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if enabled:
            logger.info(f"🔌 MCP Client '{name}' enabled: {url}")
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool on the remote MCP server.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments
        
        Returns:
            Tool result
        """
        if not self.enabled:
            logger.warning(f"MCP Client '{self.name}' is disabled")
            return None
        
        try:
            # MCP JSON-RPC 2.0 protocol
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": f"tools/{tool_name}",
                "params": kwargs
            }
            
            response = await self.client.post(self.url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                logger.error(f"MCP error from {self.name}: {data['error']}")
                return None
            
            return data.get("result")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling MCP tool '{tool_name}' on {self.name}: {e}")
            return None
    
    async def list_tools(self) -> list[dict]:
        """
        List available tools on the MCP server.
        
        Returns:
            List of tool definitions
        """
        if not self.enabled:
            return []
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            response = await self.client.post(self.url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get("result", {}).get("tools", [])
            
        except Exception as e:
            logger.error(f"Error listing tools from {self.name}: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class MCPClientManager:
    """Manages multiple MCP client connections."""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.clients: dict[str, MCPClient] = {}
        self._load_config()
    
    def _load_config(self):
        """Load MCP clients from config file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for client_config in config.get("clients", []):
                name = client_config["name"]
                url = client_config["url"]
                enabled = client_config.get("enabled", False)
                
                self.clients[name] = MCPClient(name, url, enabled)
                
        except FileNotFoundError:
            logger.warning(f"MCP clients config not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading MCP clients config: {e}")
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get MCP client by name."""
        return self.clients.get(name)
    
    async def close_all(self):
        """Close all MCP clients."""
        for client in self.clients.values():
            await client.close()
