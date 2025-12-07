"""
Analysis Agent
Agent for data analysis and pattern recognition
"""

from typing import Dict, Any, List, Optional
import json
from monitoring import get_logger
from agents.base import BaseAgent
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AnalysisAgent(BaseAgent):
    """Agent for data analysis and pattern recognition"""
    
    def __init__(self):
        """Initialize analysis agent"""
        super().__init__(
            agent_id="analysis_agent",
            name="Analysis Agent",
            capabilities=["data_analysis", "pattern_recognition", "insight_generation"],
            description="Analyzes data and generates insights"
        )
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.gemini_api_key = settings.GOOGLE_GEMINI_API_KEY
        logger.info("AnalysisAgent initialized")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute analysis task
        
        Task format:
        {
            "data": {...},  # Data to analyze
            "analysis_type": "statistical",  # statistical, pattern, trend, etc.
            "insights": true,  # Generate insights
            "visualization": false  # Generate visualization data
        }
        """
        try:
            data = task.get("data")
            if not data:
                raise ValueError("data is required")
            
            analysis_type = task.get("analysis_type", "statistical")
            generate_insights = task.get("insights", True)
            generate_visualization = task.get("visualization", False)
            
            logger.info(
                "Analysis started",
                analysis_type=analysis_type,
                data_size=len(str(data))
            )
            
            # Perform analysis based on type
            if analysis_type == "statistical":
                analysis_result = await self._statistical_analysis(data)
            elif analysis_type == "pattern":
                analysis_result = await self._pattern_analysis(data)
            elif analysis_type == "trend":
                analysis_result = await self._trend_analysis(data)
            else:
                analysis_result = await self._general_analysis(data)
            
            response = {
                "status": "success",
                "analysis_type": analysis_type,
                "analysis": analysis_result
            }
            
            if generate_insights:
                insights = await self._generate_insights(data, analysis_result)
                response["insights"] = insights
            
            if generate_visualization:
                visualization_data = self._prepare_visualization_data(data, analysis_result)
                response["visualization"] = visualization_data
            
            return response
        
        except Exception as e:
            logger.error("Analysis failed", error=str(e), exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _statistical_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform statistical analysis"""
        try:
            import numpy as np
            import pandas as pd
            
            # Convert to DataFrame if possible
            if isinstance(data, dict):
                df = pd.DataFrame([data] if not isinstance(list(data.values())[0], list) else data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame({"value": [data]})
            
            analysis = {
                "count": len(df),
                "columns": list(df.columns),
                "statistics": {}
            }
            
            # Calculate statistics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                analysis["statistics"] = df[numeric_cols].describe().to_dict()
            
            # Calculate for categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                analysis["categorical"] = {
                    col: df[col].value_counts().to_dict()
                    for col in categorical_cols[:5]  # Limit to 5 columns
                }
            
            logger.info("Statistical analysis completed", columns=len(df.columns))
            return analysis
        
        except ImportError:
            logger.warning("pandas/numpy not available, using basic analysis")
            return self._basic_analysis(data)
        except Exception as e:
            logger.error("Statistical analysis error", error=str(e))
            return self._basic_analysis(data)
    
    async def _pattern_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform pattern recognition analysis"""
        try:
            import numpy as np
            import pandas as pd
            
            # Convert to DataFrame
            if isinstance(data, dict):
                df = pd.DataFrame([data] if not isinstance(list(data.values())[0], list) else data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                return {"error": "Data format not supported for pattern analysis"}
            
            patterns = {
                "repetitions": {},
                "sequences": [],
                "correlations": {}
            }
            
            # Find repeating patterns
            for col in df.columns:
                value_counts = df[col].value_counts()
                if len(value_counts) < len(df) * 0.5:  # If less than 50% unique values
                    patterns["repetitions"][col] = value_counts.head(5).to_dict()
            
            # Find correlations for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                patterns["correlations"] = corr_matrix.to_dict()
            
            logger.info("Pattern analysis completed")
            return {"patterns": patterns}
        
        except ImportError:
            return {"error": "pandas/numpy required for pattern analysis"}
        except Exception as e:
            logger.error("Pattern analysis error", error=str(e))
            return {"error": str(e)}
    
    async def _trend_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform trend analysis"""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            if isinstance(data, dict):
                df = pd.DataFrame([data] if not isinstance(list(data.values())[0], list) else data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                return {"error": "Data format not supported for trend analysis"}
            
            trends = {}
            
            # Analyze trends in numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if len(df) > 1:
                    # Simple trend: increasing or decreasing
                    first_half = df[col].iloc[:len(df)//2].mean()
                    second_half = df[col].iloc[len(df)//2:].mean()
                    
                    if second_half > first_half * 1.1:
                        trends[col] = "increasing"
                    elif second_half < first_half * 0.9:
                        trends[col] = "decreasing"
                    else:
                        trends[col] = "stable"
            
            logger.info("Trend analysis completed")
            return {"trends": trends}
        
        except ImportError:
            return {"error": "pandas required for trend analysis"}
        except Exception as e:
            logger.error("Trend analysis error", error=str(e))
            return {"error": str(e)}
    
    async def _general_analysis(self, data: Any) -> Dict[str, Any]:
        """Perform general analysis"""
        return self._basic_analysis(data)
    
    def _basic_analysis(self, data: Any) -> Dict[str, Any]:
        """Basic analysis without external libraries"""
        if isinstance(data, dict):
            return {
                "type": "dictionary",
                "keys": list(data.keys()),
                "size": len(data)
            }
        elif isinstance(data, list):
            return {
                "type": "list",
                "length": len(data),
                "sample": data[:5] if len(data) > 5 else data
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100]
            }
    
    async def _generate_insights(
        self,
        data: Any,
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """
        Generate insights from analysis
        
        Args:
            data: Original data
            analysis_result: Analysis results
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Use LLM if available (try multiple providers)
        prompt = f"""Based on the following analysis results, generate key insights:

Analysis Results:
{json.dumps(analysis_result, indent=2)[:1000]}

Provide 3-5 key insights in bullet points."""
        
        # Try Google Gemini first
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-pro')
                
                full_prompt = "You are a data analyst that generates insights.\n\n" + prompt
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    insights_text = response.text
                    insights = [line.strip("- ") for line in insights_text.split("\n") if line.strip()]
                    if insights:
                        return insights
            except ImportError:
                logger.warning("google-generativeai package not installed")
            except Exception as e:
                logger.warning("Google Gemini API call failed, trying other providers", error=str(e))
        
        # Try OpenAI
        if self.openai_api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data analyst that generates insights."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                insights_text = response.choices[0].message.content
                insights = [line.strip("- ") for line in insights_text.split("\n") if line.strip()]
                if insights:
                    return insights
            except Exception as e:
                logger.warning("OpenAI API call failed, trying other providers", error=str(e))
        
        # Try Anthropic
        if self.anthropic_api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                
                message = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    system="You are a data analyst that generates insights.",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                insights_text = message.content[0].text
                insights = [line.strip("- ") for line in insights_text.split("\n") if line.strip()]
                if insights:
                    return insights
            except ImportError:
                logger.warning("anthropic package not installed")
            except Exception as e:
                logger.warning("Anthropic API call failed, using fallback", error=str(e))
        
        # Fallback insights
        if not insights:
            if "statistics" in analysis_result:
                insights.append("Statistical analysis completed successfully")
            if "patterns" in analysis_result:
                insights.append("Patterns identified in the data")
            if "trends" in analysis_result:
                insights.append("Trends detected in the dataset")
        
        return insights
    
    def _prepare_visualization_data(
        self,
        data: Any,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare data for visualization
        
        Args:
            data: Original data
            analysis_result: Analysis results
            
        Returns:
            Visualization data dictionary
        """
        visualization = {
            "type": "chart",
            "data": {}
        }
        
        if "statistics" in analysis_result:
            visualization["data"]["statistics"] = analysis_result["statistics"]
        
        if "patterns" in analysis_result:
            visualization["data"]["patterns"] = analysis_result["patterns"]
        
        if "trends" in analysis_result:
            visualization["data"]["trends"] = analysis_result["trends"]
        
        return visualization

