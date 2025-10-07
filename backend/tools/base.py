"""
Base classes and utilities for MCP tools implementation.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any, Generic, TypeVar, List

# Generic type variables for input and output schemas
InputType = TypeVar('InputType', bound=BaseModel)
OutputType = TypeVar('OutputType', bound=BaseModel)

class BaseTool(ABC, Generic[InputType, OutputType]):
    """
    Base class for all MCP tools.
    
    Each tool must define:
    - name: A unique identifier for the tool
    - description: Human-readable explanation of what the tool does
    - InputSchema: Pydantic model defining input parameters
    - OutputSchema: Pydantic model defining return values
    - run(): Implementation that processes inputs and returns outputs
    """
    
    name: str = "base_tool"
    description: str = "Base tool class to be extended"
    
    def __call__(self, inputs: Dict[str, Any]) -> OutputType:
        """
        Convenience method to convert dict inputs to proper schema and call run.
        
        Args:
            inputs: Dictionary of input parameters or InputSchema instance
            
        Returns:
            OutputSchema: Results following the tool's OutputSchema
        """
        # Convert dictionary to InputSchema if needed
        if isinstance(inputs, dict):
            inputs = self.InputSchema(**inputs)
        
        return self.run(inputs)
    
    @abstractmethod
    def run(self, inputs: InputType) -> OutputType:
        """
        Execute the tool's function.
        
        Args:
            inputs (InputSchema): Input parameters following the tool's InputSchema
            
        Returns:
            OutputSchema: Results following the tool's OutputSchema
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool metadata to a dictionary.
        
        Returns:
            Dict[str, Any]: Tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.InputSchema.schema(),
            "output_schema": self.OutputSchema.schema(),
        }
