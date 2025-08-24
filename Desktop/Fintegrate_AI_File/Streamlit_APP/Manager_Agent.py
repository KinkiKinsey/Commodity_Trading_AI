"""
Manager Agent Package
====================

A comprehensive package for managing and routing queries to specialized AI agents
based on intelligent analysis of user queries and ticker symbols.

This package can be imported and used in other notebooks as:
    from Manager_Agent import process_manager_query
"""

import json
import asyncio
import importlib
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os # Added for os.getenv

# Import required dependencies
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.pydantic_v1 import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: langchain_openai not available. Install with: pip install langchain-openai")

from LLM_Call_Agent import LLMCallAgent


@dataclass
class ManagerAgentResult:
    """Data class for manager agent results"""
    decision_call_market_expectation: int
    decision_call_revenue_segmentation: int
    decision_call_macro_analyst: int
    query_for_market_expectation: str
    query_for_revenue_segmentation: str
    query_for_macro_analyst: str


class ManagerAgentResultPydantic(BaseModel):
    """Pydantic model for structured LLM output"""
    Decision_call_market_expectation: int = Field(description="1 if call market expectation agent, 0 otherwise")
    Decision_call_revenue_segmentation: int = Field(description="1 if call revenue segmentation agent, 0 otherwise")
    Decision_call_macro_analyst: int = Field(description="1 if call macro analyst agent, 0 otherwise")
    quer_for_market_expectation: str = Field(description="Query for market expectation agent")
    quer_for_revenue_segmentation: str = Field(description="Query for revenue segmentation agent")
    quer_for_macro_analyst: str = Field(description="Query for macro analyst agent")


class ManagerAgent:
    """
    Main Manager Agent class for intelligent query routing and agent coordination
    """
    
    def __init__(self, redis_config: Optional[Dict] = None, user_id: Optional[str] = None):
        """
        Initialize the Manager Agent
        
        Args:
            redis_config: Redis configuration dictionary with host, port, password
            user_id: User identifier to pass to all sub-agents
        """
        self.redis_config = redis_config or {
            'host': 'redis-16376.crce197.us-east-2-1.ec2.redns.redis-cloud.com',
            'port': 16376,
            'password': 'rl8242B4UItBhFzgHW5APEqZnkYoaEZv'
        }
        
        # Store user_id for passing to sub-agents
        self.user_id = user_id or "Fintegrate_AI_Default"
        self.task_id = f"task_{int(datetime.datetime.now().timestamp())}"
        
        # Frontend Redis Database (Separate from stock trend database) - SAME AS MARKET EXPECTATION AGENT
        self.frontend_redis = None
        self.frontend_redis_host = "redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com"
        self.frontend_redis_port = 16204
        self.frontend_redis_username = "default"
        self.frontend_redis_password = "9rHiMKl63iYK9ja4qja6ZjnamuixS4UG"
        
        # Initialize Frontend Redis for progress tracking and result storage
        self._setup_frontend_redis()
        
        # Get API keys from environment variables
        openai_api_key = os.getenv('OPENAI_API_KEY')
        deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        
        # Initialize LLM Call Agent
        self.manager_agent = LLMCallAgent(
            default_provider="deepseek",
            default_model="deepseek-chat",
            openai_api_key=openai_api_key,
            deepseek_api_key=deepseek_api_key
        )
        
        print(f"🔑 API Keys Status:")
        print(f"   - DeepSeek: {'✅ Available' if deepseek_api_key else '❌ Missing'}")
        print(f"   - OpenAI: {'✅ Available' if openai_api_key else '❌ Missing'}")
        
        # Initialize structured LLM if langchain is available
        self.structured_llm = None
        if LANGCHAIN_AVAILABLE:
            self._setup_structured_llm()
    
    def _setup_frontend_redis(self):
        """Setup Frontend Redis connection for progress tracking and result storage (SAME AS MARKET EXPECTATION AGENT)"""
        try:
            import redis
            self.frontend_redis = redis.Redis(
                host=self.frontend_redis_host,
                port=self.frontend_redis_port,
                username=self.frontend_redis_username,
                password=self.frontend_redis_password,
                decode_responses=True
            )
            # Test connection
            self.frontend_redis.ping()
            print(f"✅ Manager Agent Frontend Redis connected: {self.frontend_redis_host}:{self.frontend_redis_port}")
        except Exception as e:
            print(f"❌ Manager Agent Frontend Redis connection failed: {e}")
            self.frontend_redis = None
    
    def _update_progress(self, stage: str, status: str, percentage: int, details: str = ""):
        """
        Update progress in Frontend Redis - separate from stock trend database (SAME AS MARKET EXPECTATION AGENT)
        
        Args:
            stage: Current step (e.g., "query_analysis", "agent_execution")
            status: Status (e.g., "started", "completed", "failed", "in_progress")
            percentage: Progress percentage (0-100)
            details: Additional details
        """
        if not self.frontend_redis:
            print("⚠️ Frontend Redis not available for progress tracking")
            return
        
        try:
            progress_data = {
                "user_id": self.user_id,
                "task_id": self.task_id,
                "step": stage,
                "status": status,
                "progress": percentage,
                "details": details,
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": "manager_agent"  # Identify this agent's data
            }
            
            # Store progress update in frontend Redis - separate from stock trend database
            progress_key = f"manager_frontend_progress:{self.user_id}"
            
            # Get existing progress data
            existing_data = self.frontend_redis.hgetall(progress_key)
            
            # Create updated data structure
            updated_data = {}
            
            # Keep existing data from other agents
            for key, value in existing_data.items():
                try:
                    data = json.loads(value)
                    # Only keep data from other agents
                    if data.get("agent") != "manager_agent":
                        updated_data[key] = value
                except:
                    # Keep non-JSON data (legacy)
                    updated_data[key] = value
            
            # Add/update Manager Agent data
            manager_agent_key = f"manager_agent:{stage}"
            updated_data[manager_agent_key] = json.dumps(progress_data)
            
            # Store all data back to Frontend Redis
            if updated_data:
                self.frontend_redis.hset(progress_key, mapping=updated_data)
            
            # Set expiry to clean up old progress (24 hours)
            self.frontend_redis.expire(progress_key, 86400)
            
            print(f"📊 Frontend Progress Update: {stage} - {status} ({percentage}%) - Agent: Manager Agent")
            
        except Exception as e:
            print(f"❌ Failed to update frontend progress: {e}")
    
    def _store_manager_result(self, result_data: Dict[str, Any]):
        """
        Store Manager Agent result in Frontend Redis (SAME AS MARKET EXPECTATION AGENT)
        
        Args:
            result_data: Complete result data to store
        """
        if not self.frontend_redis:
            print("⚠️ Frontend Redis not available for result storage")
            return
        
        try:
            # Convert dataclass to dict if needed (fix for JSON serialization)
            def convert_dataclass_to_dict(obj):
                if hasattr(obj, '__dict__'):
                    return {k: convert_dataclass_to_dict(v) for k, v in obj.__dict__.items()}
                elif isinstance(obj, list):
                    return [convert_dataclass_to_dict(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: convert_dataclass_to_dict(v) for k, v in obj.items()}
                else:
                    return obj
            
            # Convert the result data to ensure JSON serialization works
            serializable_data = convert_dataclass_to_dict(result_data)
            
            # Add metadata
            serializable_data["user_id"] = self.user_id
            serializable_data["task_id"] = self.task_id
            serializable_data["timestamp"] = datetime.datetime.now().isoformat()
            serializable_data["agent"] = "manager_agent"
            
            # Store in Frontend Redis with user_id prefix (SAME AS MARKET EXPECTATION AGENT)
            result_key = f"manager_result:{self.user_id}"
            self.frontend_redis.set(result_key, json.dumps(serializable_data))
            
            # Set expiry to clean up old results (24 hours)
            self.frontend_redis.expire(result_key, 86400)
            
            print(f"✅ Manager result stored in Frontend Redis: {result_key}")
            
        except Exception as e:
            print(f"❌ Failed to store manager result: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_structured_llm(self):
        """Setup structured LLM for intelligent routing"""
        try:
            deepseek_api_key = self.manager_agent.deepseek_api_key
            llm = ChatOpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com",
                model="deepseek-chat",
                temperature=0,
                timeout=60,
            )
            self.structured_llm = llm.with_structured_output(ManagerAgentResultPydantic)
        except Exception as e:
            print(f"Warning: Could not setup structured LLM: {e}")
            self.structured_llm = None
    
    def process_manager_query(self, user_query: str, ticker: str) -> ManagerAgentResult:
        """
        Process a user query and intelligently route to appropriate agents
        
        Args:
            user_query: The user's question or query
            ticker: Stock ticker symbol
            
        Returns:
            ManagerAgentResult with routing decisions and generated queries
        """
        if not self.structured_llm:
            # Fallback to simple routing logic
            return self._fallback_routing(user_query, ticker)
        
        # Intelligent routing prompt
        prompt = f"""
        You are a Manager Agent that analyzes user queries and decides which specialized agents to call.
        
        USER QUERY: "{user_query}"
        TICKER: {ticker}
        
        AVAILABLE AGENTS AND THEIR CAPABILITIES:
        
        1. MARKET EXPECTATION AGENT:
           - Database: Stock trend time intervals, price behavior, micro/macro events, timeline segmentation
           - Best for: Finding similar historical trends based on events, policies, earnings
           - Example queries: "Given tariff cuts, find similar timeline trends with similar macro/micro events"
           - Decision: Call if query involves market trends, price behavior, or historical pattern matching
        
        2. REVENUE SEGMENTATION AGENT:
           - Database: Revenue breakdown (GPU %, Data Center %, etc.), customer segments
           - Best for: Revenue impact analysis of corporate partnerships, service changes, market shifts
           - Example queries: "How will Microsoft partnership affect CRWV revenue segments?"
           - Decision: Call if query involves revenue drivers, partnerships, or business model changes
        
        3. MACRO ANALYST AGENT:
           - Database: Macroeconomic indicators, policy changes, economic environment data
           - Best for: Economic factors affecting stock performance, policy impacts
           - Example queries: "How do interest rates affect CRWV?"
           - Decision: Call if query involves economic environment, policies, or macro factors
        
        YOUR TASK:
        1. Analyze the user query to determine which agents are relevant
        2. Generate specific, targeted queries for each relevant agent
        3. Set decision flags (1=call, 0=don't call) for each agent
        4. Ensure queries are specific and actionable for each agent's database
        
        OUTPUT FORMAT:
        - Decision_call_market_expectation: 1 if query involves trends/patterns, 0 otherwise
        - Decision_call_revenue_segmentation: 1 if query involves revenue/business model, 0 otherwise  
        - Decision_call_macro_analyst: 1 if query involves economic environment, 0 otherwise
        - Generate specific queries only for agents you decide to call (1)
        - For agents you don't call (0), use "N/A" as the query
        """
        
        try:
            result = self.structured_llm.invoke(prompt)
            return ManagerAgentResult(
                decision_call_market_expectation=result.Decision_call_market_expectation,
                decision_call_revenue_segmentation=result.Decision_call_revenue_segmentation,
                decision_call_macro_analyst=result.Decision_call_macro_analyst,
                query_for_market_expectation=result.quer_for_market_expectation,
                query_for_revenue_segmentation=result.quer_for_revenue_segmentation,
                query_for_macro_analyst=result.quer_for_macro_analyst
            )
        except Exception as e:
            print(f"Error in structured LLM call: {e}")
            return self._fallback_routing(user_query, ticker)
    
    def _fallback_routing(self, user_query: str, ticker: str) -> ManagerAgentResult:
        """Fallback routing logic when structured LLM is not available"""
        query_lower = user_query.lower()
        
        # Simple keyword-based routing
        market_keywords = ['trend', 'pattern', 'historical', 'price', 'behavior', 'earnings']
        revenue_keywords = ['revenue', 'partnership', 'business model', 'customer', 'service']
        macro_keywords = ['interest rate', 'federal reserve', 'economic', 'policy', 'macro']
        
        decision_market = any(keyword in query_lower for keyword in market_keywords)
        decision_revenue = any(keyword in query_lower for keyword in revenue_keywords)
        decision_macro = any(keyword in query_lower for keyword in macro_keywords)
        
        return ManagerAgentResult(
            decision_call_market_expectation=1 if decision_market else 0,
            decision_call_revenue_segmentation=1 if decision_revenue else 0,
            decision_call_macro_analyst=1 if decision_macro else 0,
            query_for_market_expectation=user_query if decision_market else "N/A",
            query_for_revenue_segmentation=user_query if decision_revenue else "N/A",
            query_for_macro_analyst=user_query if decision_macro else "N/A"
        )
    
    def create_agent_calling_form(self, result: ManagerAgentResult) -> Dict[str, Any]:
        """
        Create the agent calling form based on routing decisions
        
        Args:
            result: ManagerAgentResult from process_manager_query
            
        Returns:
            Dictionary mapping agent names to their queries
        """
        decision_list = [
            result.decision_call_market_expectation,
            result.decision_call_revenue_segmentation,
            result.decision_call_macro_analyst
        ]
        
        agent_list = [
            "Market_Expectation_Agent",
            "Revenue_Segmentation_Agent", 
            "Macro_Analyst_Agent"
        ]
        
        query_list = [
            result.query_for_market_expectation,
            result.query_for_revenue_segmentation,
            result.query_for_macro_analyst
        ]
        
        agents_calling_form = {}
        for i in range(len(decision_list)):
            if decision_list[i] == 1:
                agents_calling_form[agent_list[i]] = 1
                agents_calling_form[agent_list[i] + "_Query"] = query_list[i]
        
        return agents_calling_form
    
    async def call_agents_dynamically(self, agents_calling_form: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """
        TRUE MULTIPROCESSING: Dynamically call agents SIMULTANEOUSLY and collect results
        
        Args:
            agents_calling_form: Dictionary from create_agent_calling_form
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with results from all called agents
        """
        agents_results = {}
        
        print("🚀 Starting TRUE PARALLEL Agent Execution...")
        print("=" * 60)
        
        # Update progress for parallel execution
        if hasattr(self, '_update_progress'):
            self._update_progress("parallel_execution", "started", 65, "Starting parallel agent execution")
        
        # Extract agent decisions and queries
        agent_decisions = {k: v for k, v in agents_calling_form.items() if not k.endswith('_Query')}
        
        # Create tasks for ALL agents that need to be called
        async def execute_single_agent(agent_name: str, query: str):
            try:
                start_time = asyncio.get_event_loop().time()
                print(f"🔄 Starting {agent_name} at {start_time:.2f}s...")
                result = await self._call_specific_agent(agent_name, query, ticker)
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                print(f"✅ {agent_name} completed successfully in {duration:.2f}s")
                return agent_name, result
            except Exception as e:
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                print(f"❌ {agent_name} failed after {duration:.2f}s: {e}")
                return agent_name, f"Error: {str(e)}"
        
        # Collect all tasks that need to run
        tasks = []
        for agent_name, decision in agent_decisions.items():
            if decision == 1:
                query_key = f"{agent_name}_Query"
                agent_query = agents_calling_form.get(query_key, "N/A")
                tasks.append(execute_single_agent(agent_name, agent_query))
            else:
                print(f"⏭️ Skipping {agent_name} (decision = 0)")
        
        print(f"📊 Executing {len(tasks)} agents in TRUE PARALLEL...")
        print(f"🚀 Launching ALL agents SIMULTANEOUSLY at {asyncio.get_event_loop().time():.2f}s...")
        
        # Execute ALL agents SIMULTANEOUSLY using asyncio.gather
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update progress for completion
            if hasattr(self, '_update_progress'):
                self._update_progress("parallel_execution", "completed", 75, f"All {len(tasks)} agents completed execution")
            
            # Process results
            for agent_name, result in results:
                if isinstance(result, Exception):
                    agents_results[f"{agent_name}_Result"] = f"Error: {str(result)}"
                else:
                    agents_results[f"{agent_name}_Result"] = result
        
        print("\n" + "=" * 60)
        print("📊 Final Results Summary:")
        print("=" * 60)
        
        for key, value in agents_results.items():
            print(f"{key}: {str(value)[:200]}...")
        
        return agents_results
    
    async def _call_specific_agent(self, agent_name: str, query: str, ticker: str) -> Any:
        """
        Call a specific agent based on name with user_id support
        
        Args:
            agent_name: Name of the agent to call
            query: Query to send to the agent
            ticker: Stock ticker symbol
            
        Returns:
            Result from the agent
        """
        if agent_name == "Market_Expectation_Agent":
            from Market_Expectation_Agent import MarketExpectationAgent
            agent = MarketExpectationAgent(
                redis_host=self.redis_config['host'],
                redis_port=self.redis_config['port'],
                redis_password=self.redis_config['password'],
                user_id=self.user_id  # ✅ Pass user_id to Market Expectation Agent
            )
            # ✅ This is already async - good!
            result = await agent.process_query(query, ticker)
            agent.close()
            return result.get('stock_read_result', 'No result')
            
        elif agent_name == "Revenue_Segmentation_Agent":
            from Revenue_Segmentation_Read_Agent import RevenueSegmentationAnalystAgent
            agent = RevenueSegmentationAnalystAgent(
                redis_host=self.redis_config['host'],
                redis_port=self.redis_config['port'],
                redis_password=self.redis_config['password'],
                user_id=self.user_id  # ✅ Pass user_id to Revenue Segmentation Agent
            )
            # ❌ This is SYNC - needs to be made async!
            # Use asyncio.to_thread to make sync calls non-blocking
            import asyncio
            result = await asyncio.to_thread(agent.process_natural_query, query, ticker)
            agent.close()
            return result
            
        elif agent_name == "Macro_Analyst_Agent":
            from Macro_Analyst_Agent import MacroAnalystAgent
            agent = MacroAnalystAgent(user_id=self.user_id)  # ✅ Use stored user_id instead of hardcoded
            # ❌ This is SYNC - needs to be made async!
            # Use asyncio.to_thread to make sync calls non-blocking
            import asyncio
            # ✅ Call run_macro_analysis instead of process_macro_query to ensure results are stored!
            result = await asyncio.to_thread(agent.run_macro_analysis, query)
            if hasattr(agent, 'redis_client') and agent.redis_client:
                agent.redis_client.close()
            return result.get('analysis', 'No result')
        
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    
    def print_analysis_results(self, user_query: str, ticker: str, result: ManagerAgentResult):
        """Print formatted analysis results"""
        print("🤖 Manager Agent Analysis Results:")
        print("=" * 50)
        print(f"User Query: {user_query}")
        print(f"Ticker: {ticker}")
        print("\n📊 Agent Routing Decisions:")
        print(f"Market Expectation Agent: {'✅ CALL' if result.decision_call_market_expectation else '❌ SKIP'}")
        print(f"Revenue Segmentation Agent: {'✅ CALL' if result.decision_call_revenue_segmentation else '❌ SKIP'}")
        print(f"Macro Analyst Agent: {'✅ CALL' if result.decision_call_macro_analyst else '❌ SKIP'}")
        
        print("\n🔍 Generated Queries:")
        if result.decision_call_market_expectation:
            print(f"Market: {result.query_for_market_expectation}")
        if result.decision_call_revenue_segmentation:
            print(f"Revenue: {result.query_for_revenue_segmentation}")
        if result.decision_call_macro_analyst:
            print(f"Macro: {result.query_for_macro_analyst}")
    
    def close(self):
        """Close Frontend Redis connection (SAME AS MARKET EXPECTATION AGENT)"""
        if self.frontend_redis:
            try:
                self.frontend_redis.close()
                print("🔚 Manager Agent Frontend Redis connection closed")
            except Exception as e:
                print(f"❌ Error closing Frontend Redis connection: {e}")
    
    def get_stored_result(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored Manager Agent result from Frontend Redis (SAME AS MARKET EXPECTATION AGENT)
        
        Returns:
            Stored result data or None if not found
        """
        if not self.frontend_redis:
            return None
        
        try:
            result_key = f"manager_result:{self.user_id}"
            result_data = self.frontend_redis.get(result_key)
            
            if result_data:
                return json.loads(result_data)
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to retrieve stored result: {e}")
            return None
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve current progress from Frontend Redis (SAME AS MARKET EXPECTATION AGENT)
        
        Returns:
            Current progress data or None if not found
        """
        if not self.frontend_redis:
            return None
        
        try:
            progress_key = f"manager_frontend_progress:{self.user_id}"
            progress_data = self.frontend_redis.hgetall(progress_key)
            
            if progress_data:
                result = {}
                for key, data_str in progress_data.items():
                    try:
                        result[key] = json.loads(data_str)
                    except:
                        result[key] = {"step": key, "data": data_str}
                return result
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to retrieve progress: {e}")
            return None
    
    def test_frontend_redis_storage(self) -> bool:
        """
        Test if Frontend Redis storage is working properly (SAME AS MARKET EXPECTATION AGENT)
        
        Returns:
            True if storage test passes, False otherwise
        """
        if not self.frontend_redis:
            print("❌ No Frontend Redis connection available")
            return False
        
        try:
            # Test data
            test_data = {
                "test": "data",
                "timestamp": datetime.datetime.now().isoformat(),
                "user_id": self.user_id,
                "task_id": self.task_id,
                "agent": "manager_agent"
            }
            
            # Test key
            test_key = f"manager_test:{self.user_id}"
            
            # Store test data
            self.frontend_redis.set(test_key, json.dumps(test_data))
            
            # Retrieve test data
            retrieved_data = self.frontend_redis.get(test_key)
            
            if retrieved_data:
                retrieved_dict = json.loads(retrieved_data)
                if retrieved_dict["test"] == "data":
                    print(f"✅ Frontend Redis storage test passed for user {self.user_id}")
                    # Clean up test data
                    self.frontend_redis.delete(test_key)
                    return True
                else:
                    print("❌ Frontend Redis storage test failed - data mismatch")
                    return False
            else:
                print("❌ Frontend Redis storage test failed - no data retrieved")
                return False
                
        except Exception as e:
            print(f"❌ Frontend Redis storage test failed: {e}")
            return False


# Convenience functions for easy import
def process_manager_query(user_query: str, ticker: str, redis_config: Optional[Dict] = None, user_id: Optional[str] = None) -> ManagerAgentResult:
    """
    Convenience function to process a manager query
    
    Args:
        user_query: The user's question or query
        ticker: Stock ticker symbol
        redis_config: Optional Redis configuration
        user_id: User identifier to pass to all sub-agents
        
    Returns:
        ManagerAgentResult with routing decisions and generated queries
    """
    manager = ManagerAgent(redis_config, user_id)
    return manager.process_manager_query(user_query, ticker)


def create_agent_calling_form(result: ManagerAgentResult, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to create agent calling form
    
    Args:
        result: ManagerAgentResult from process_manager_query
        user_id: User identifier to pass to all sub-agents
        
    Returns:
        Dictionary mapping agent names to their queries
    """
    manager = ManagerAgent(user_id=user_id)
    return manager.create_agent_calling_form(result)


async def call_agents_dynamically(agents_calling_form: Dict[str, Any], ticker: str, redis_config: Optional[Dict] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to call agents dynamically with AUTOMATIC MULTIPROCESSING
    
    Args:
        agents_calling_form: Dictionary from create_agent_calling_form
        ticker: Stock ticker symbol
        redis_config: Optional Redis configuration
        user_id: User identifier to pass to all sub-agents
        
    Returns:
        Dictionary with results from all called agents
    """
    manager = ManagerAgent(redis_config, user_id)
    return await manager.call_agents_dynamically(agents_calling_form, ticker)


# ===== MAIN FUNCTION - AUTOMATIC MULTIPROCESSING =====
async def analyze_with_multiprocessing(user_query: str, ticker: str, redis_config: Optional[Dict] = None, user_id: Optional[str] = None, manager_instance: Optional['ManagerAgent'] = None) -> Dict[str, Any]:
    """
    🚀 MAIN FUNCTION: Complete analysis with AUTOMATIC MULTIPROCESSING
    
    This function does EVERYTHING automatically:
    1. Analyzes your query
    2. Routes to appropriate agents  
    3. Runs ALL agents in parallel
    4. Returns combined results
    
    Args:
        user_query: Your question
        ticker: Stock symbol
        redis_config: Optional Redis config
        user_id: User identifier to pass to all sub-agents
        manager_instance: Optional existing ManagerAgent instance to use
        
    Returns:
        Complete results from all sub-agents
    """
    print("🚀 MANAGER AGENT - AUTOMATIC MULTIPROCESSING ANALYSIS")
    print("=" * 80)
    print(f"📝 Query: {user_query}")
    print(f"🎯 Ticker: {ticker}")
    print(f"👤 User ID: {user_id or 'Default'}")
    print("=" * 80)
    
    # Use existing ManagerAgent instance or create new one
    if manager_instance:
        manager = manager_instance
        print("✅ Using existing ManagerAgent instance")
    else:
        manager = ManagerAgent(redis_config, user_id)
        print("🆕 Created new ManagerAgent instance")
    
    # Step 1: Process query and get routing decisions
    print("\n🔍 STEP 1: Analyzing query and routing to sub-agents...")
    manager._update_progress("query_analysis", "started", 10, "Analyzing query and routing to sub-agents")
    result = process_manager_query(user_query, ticker, redis_config, user_id)
    
    # Display routing decisions
    print(f"\n📊 ROUTING DECISIONS:")
    print(f"   Market Expectation: {'✅ CALL' if result.decision_call_market_expectation else '❌ SKIP'}")
    print(f"   Revenue Segmentation: {'✅ CALL' if result.decision_call_revenue_segmentation else '❌ SKIP'}")
    print(f"   Macro Analyst: {'✅ CALL' if result.decision_call_macro_analyst else '❌ SKIP'}")
    
    manager._update_progress("query_analysis", "completed", 20, "Query analysis and routing completed")
    
    # Step 2: Create agent calling form
    print(f"\n📋 STEP 2: Creating agent calling form...")
    manager._update_progress("agent_planning", "started", 30, "Creating agent calling form")
    calling_form = create_agent_calling_form(result, user_id)
    print(f"   Agents to call: {list(calling_form.keys())}")
    manager._update_progress("agent_planning", "completed", 40, f"Agent calling form created for {len(calling_form)//2} agents")
    
    # Step 3: Execute sub-agents with AUTOMATIC MULTIPROCESSING
    print(f"\n🚀 STEP 3: Executing sub-agents with AUTOMATIC MULTIPROCESSING...")
    manager._update_progress("agent_execution", "started", 50, "Starting parallel agent execution")
    try:
        # This automatically uses multiprocessing - no extra code needed!
        manager._update_progress("agent_execution", "in_progress", 60, "Executing agents in parallel")
        final_results = await call_agents_dynamically(calling_form, ticker, redis_config, user_id)
        
        manager._update_progress("agent_execution", "completed", 80, f"All agents completed execution")
        
        # Display comprehensive results
        print("\n" + "=" * 80)
        print(" COMPLETE SUB-AGENT ANALYSIS RESULTS (MULTIPROCESSING)")
        print("=" * 80)
        
        for agent_name, agent_result in final_results.items():
            print(f"\n{agent_name}:")
            print(f"{'=' * 50}")
            
            if isinstance(agent_result, str) and agent_result.startswith("Error"):
                print(f"❌ {agent_result}")
            else:
                print(f"✅ {str(agent_result)[:500]}...")
        
        # Summary
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"   Total Agents Executed: {len(final_results)}")
        successful = len([r for r in final_results.values() if not str(r).startswith("Error")])
        failed = len([r for r in final_results.values() if str(r).startswith("Error")])
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        # Return complete results
        complete_result = {
            "routing_analysis": result,
            "agent_results": final_results,
            "execution_summary": {
                "total_agents_executed": len(final_results),
                "successful_executions": successful,
                "failed_executions": failed
            }
        }
        
        # Store result in Redis (same pattern as other agents)
        manager._update_progress("result_storage", "started", 90, "Storing final results")
        manager._store_manager_result(complete_result)
        manager._update_progress("result_storage", "completed", 100, "Analysis complete - results stored")
        
        return complete_result
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        manager._update_progress("error_handling", "failed", 0, f"Execution failed: {str(e)}")
        return None


# ===== ULTRA-SIMPLE FUNCTION =====
async def quick_analysis(user_query: str, ticker: str, user_id: Optional[str] = None, redis_config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    🎯 ULTRA-SIMPLE: Just input query and ticker, get multiprocessing results automatically
    
    Args:
        user_query: Your question
        ticker: Stock symbol
        user_id: User identifier to pass to all sub-agents
        redis_config: Optional Redis configuration
        
    Returns:
        Complete analysis from all relevant agents with multiprocessing
    """
    # Create ManagerAgent instance for progress tracking and result storage
    manager = ManagerAgent(redis_config, user_id)
    
    try:
        # Pass the manager instance to ensure progress tracking works
        result = await analyze_with_multiprocessing(user_query, ticker, redis_config, user_id, manager)
        return result
    finally:
        # Always close the manager to clean up Redis connections
        manager.close()


# ===== CONVENIENCE FUNCTIONS FOR RETRIEVING STORED DATA =====
def get_manager_result(user_id: str, redis_config: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to retrieve stored Manager Agent result
    
    Args:
        user_id: User identifier
        redis_config: Optional Redis configuration
        
    Returns:
        Stored result data or None if not found
    """
    manager = ManagerAgent(redis_config, user_id)
    result = manager.get_stored_result()
    manager.close()
    return result


def get_manager_progress(user_id: str, redis_config: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to retrieve current Manager Agent progress
    
    Args:
        user_id: User identifier
        redis_config: Optional Redis configuration
        
    Returns:
        Current progress data or None if not found
    """
    manager = ManagerAgent(redis_config, user_id)
    progress = manager.get_progress()
    manager.close()
    return progress


def test_manager_frontend_redis_storage(user_id: str, redis_config: Optional[Dict] = None) -> bool:
    """
    Test if Manager Agent Frontend Redis storage is working properly (SAME AS MARKET EXPECTATION AGENT)
    
    Args:
        user_id: User identifier
        redis_config: Optional Redis configuration
        
    Returns:
        True if storage test passes, False otherwise
    """
    manager = ManagerAgent(redis_config, user_id)
    result = manager.test_frontend_redis_storage()
    manager.close()
    return result


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    async def main():
        print("🚀 MANAGER AGENT - AUTOMATIC MULTIPROCESSING DEMO")
        print("=" * 80)
        
        # Example query
        user_question = "Federal Reserve Powell indicates conditions, 'may warrant' interest rate cuts as Fed proceeds 'carefully'"
        # Use a variable instead of hardcoded ticker
        demo_ticker = "DEMO"  # Changed from hardcoded "MSTR"
        
        print(f"📝 Query: {user_question}")
        print(f"🎯 Ticker: {demo_ticker}")
        print("\n" + "=" * 80)
        
        # OPTION 1: Use the ultra-simple function (RECOMMENDED)
        print("🎯 OPTION 1: Ultra-simple with automatic multiprocessing")
        print("-" * 50)
        complete_results = await quick_analysis(user_question, demo_ticker, user_id="Demo_User_123")
        
        if complete_results:
            print("\n✅ ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"📊 Total agents executed: {complete_results['execution_summary']['total_agents_executed']}")
        else:
            print("\n❌ Analysis failed")
        
        print("\n" + "=" * 80)
        
        # OPTION 2: Use the detailed function
        print("🔍 OPTION 2: Detailed analysis with automatic multiprocessing")
        print("-" * 50)
        detailed_results = await analyze_with_multiprocessing(user_question, demo_ticker, user_id="Demo_User_456")
        
        if detailed_results:
            print("\n✅ DETAILED ANALYSIS COMPLETED!")
        else:
            print("\n❌ Detailed analysis failed")
    
    # Run example
    asyncio.run(main())
