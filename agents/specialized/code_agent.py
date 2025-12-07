"""
Code Generation Agent
Agent for generating code based on requirements
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
from monitoring import get_logger
from agents.base import BaseAgent
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class CodeGenerationAgent(BaseAgent):
    """Agent for generating code files"""
    
    def __init__(self):
        """Initialize code generation agent"""
        super().__init__(
            agent_id="code_generation_agent",
            name="Code Generation Agent",
            capabilities=["code_generation", "file_creation", "code_analysis"],
            description="Generates code files based on requirements and project context"
        )
        self.openai_api_key = settings.OPENAI_API_KEY
        logger.info("CodeGenerationAgent initialized")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code generation task
        
        Task format:
        {
            "file_path": "path/to/file.py",
            "description": "Generate a function that...",
            "language": "python",
            "context": {...}  # Optional project context
        }
        """
        try:
            file_path = task.get("file_path")
            description = task.get("description", "")
            language = task.get("language", "python")
            context = task.get("context", {})
            
            if not file_path:
                raise ValueError("file_path is required")
            
            logger.info(
                "Code generation started",
                file_path=file_path,
                language=language
            )
            
            # Generate code using LLM (simplified implementation)
            # In production, this would use OpenAI/Anthropic API
            generated_code = await self._generate_code(
                description=description,
                language=language,
                context=context,
                file_path=file_path
            )
            
            # Optionally write to file
            write_to_file = task.get("write_to_file", False)
            if write_to_file and generated_code:
                self._write_code_to_file(file_path, generated_code)
            
            return {
                "status": "success",
                "file_path": file_path,
                "code": generated_code,
                "language": language,
                "message": f"Code generated for {file_path}"
            }
        
        except Exception as e:
            logger.error("Code generation failed", error=str(e), exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_code(
        self,
        description: str,
        language: str,
        context: Dict[str, Any],
        file_path: str
    ) -> str:
        """
        Generate code using LLM
        
        Args:
            description: Code description/requirements
            language: Programming language
            context: Project context
            file_path: Target file path
            
        Returns:
            Generated code
        """
        # Simplified code generation
        # In production, integrate with OpenAI/Anthropic API
        
        if self.openai_api_key:
            # Use OpenAI API if available
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)
                
                prompt = f"""Generate {language} code for the following requirement:

{description}

File path: {file_path}

Context: {context if context else 'No additional context'}

Generate complete, production-ready code with proper documentation."""
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"You are an expert {language} developer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                return response.choices[0].message.content
            except Exception as e:
                logger.warning("OpenAI API call failed, using fallback", error=str(e))
        
        # Fallback: Generate template code
        return self._generate_template_code(description, language, file_path)
    
    def _generate_template_code(
        self,
        description: str,
        language: str,
        file_path: str
    ) -> str:
        """Generate template code as fallback"""
        if language == "python":
            return f'''"""
{description}
"""

def main():
    """Main function"""
    pass

if __name__ == "__main__":
    main()
'''
        elif language == "javascript":
            return f'''// {description}

function main() {{
    // Implementation
}}

module.exports = {{ main }};
'''
        else:
            return f"# {description}\n# Code generation for {file_path}\n"
    
    def _write_code_to_file(self, file_path: str, code: str):
        """Write generated code to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.info("Code written to file", file_path=file_path)
        except Exception as e:
            logger.error("Failed to write code to file", file_path=file_path, error=str(e))
            raise
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze project structure for context
        
        Args:
            project_path: Path to project root
            
        Returns:
            Project analysis dictionary
        """
        try:
            project_root = Path(project_path)
            
            analysis = {
                "project_path": str(project_root),
                "files": [],
                "structure": {},
                "dependencies": []
            }
            
            # Analyze project structure
            for root, dirs, files in os.walk(project_root):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(project_root)
                    
                    analysis["files"].append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix
                    })
            
            # Check for dependency files
            dependency_files = ["requirements.txt", "package.json", "Pipfile", "poetry.lock"]
            for dep_file in dependency_files:
                dep_path = project_root / dep_file
                if dep_path.exists():
                    analysis["dependencies"].append(str(dep_path))
            
            logger.info("Project analysis completed", project_path=project_path, files_count=len(analysis["files"]))
            return analysis
        
        except Exception as e:
            logger.error("Project analysis failed", project_path=project_path, error=str(e))
            return {"error": str(e)}
