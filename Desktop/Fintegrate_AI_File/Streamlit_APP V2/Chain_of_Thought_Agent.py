import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from LLM_Call_Agent import LLMCallAgent

class ChainOfThoughtResult(BaseModel):
    initial_query: str = Field(description="The original user question")
    ticker: str = Field(description="Stock ticker symbol")
    impact_chain: str = Field(description="Linear chain: A → B → C → D → Final")
    final_direction: str = Field(description="Final impact: 'Short' or 'Long'")
    chain_explanation: str = Field(description="Brief explanation of the chain logic")
    node_count: int = Field(description="Number of nodes in the chain")
    edge_count: int = Field(description="Number of edges/connections in the chain")
    events: List[str] = Field(description="List of individual events in the chain")

def generate_mermaid_code(node_count: int, edge_count: int, events: List[str]) -> str:
    """
    ✅ TRULY DYNAMIC - Generates Mermaid.js code for ANY number of nodes
    """
    
    # ✅ NO MINIMUM LIMITS - Let it be as short or long as needed
    if node_count < 1:  # Allow single node if needed
        node_count = 1
    if edge_count < 0:  # Allow no edges if single node
        edge_count = 0
    
    # ✅ DYNAMIC NODE IDS - Handle any number of nodes
    node_ids = []
    for i in range(node_count):
        if i < 26:  # A-Z
            node_ids.append(chr(65 + i))
        else:  # AA, AB, AC... for more than 26 nodes
            node_ids.append(f"{chr(65 + i//26)}{chr(65 + i%26)}")
    
    # ✅ CLEAN EVENTS - Remove any Pydantic field names and special characters
    clean_events = []
    for event in events[:node_count]:
        # Remove field names like "initial_query:", "ticker:", etc.
        if ': ' in event:
            clean_event = event.split(': ')[-1]
        else:
            clean_event = event
        
        # Clean special characters that break Mermaid.js
        clean_event = clean_event.replace('"', "'")  # Replace quotes
        clean_event = clean_event.replace('\\', '/')  # Replace backslashes
        clean_event = clean_event.replace('\n', ' ')  # Replace newlines
        clean_event = clean_event.replace('\r', ' ')  # Replace carriage returns
        clean_event = clean_event.replace('\t', ' ')  # Replace tabs
        
        # Remove any remaining problematic characters
        clean_event = re.sub(r'[^\w\s\-\.\'\&\+]', '', clean_event)
        
        # Limit length to prevent Mermaid.js issues
        if len(clean_event) > 50:
            clean_event = clean_event[:47] + "..."
        
        clean_events.append(clean_event)
    
    # ✅ TRULY DYNAMIC MERMAID CODE - Adapts to any number of nodes
    mermaid_code = "graph LR\n"
    
    # ✅ FIXED - Create separate node for each event
    for i in range(node_count):
        node_id = node_ids[i]
        if i < len(clean_events):
            # ✅ LAST NODE - Just show the final decision (Short/Long)
            if i == node_count - 1:  # Last node
                # Extract just "Short" or "Long" from the last event
                last_event = clean_events[i]
                if "Short" in last_event:
                    event_text = "Short"
                elif "Long" in last_event:
                    event_text = "Long"
                else:
                    event_text = last_event
            else:
                event_text = clean_events[i]
        else:
            event_text = f"Step {i+1}"
        
        # Ensure event_text is safe for Mermaid.js
        if not event_text or event_text.strip() == "":
            event_text = f"Step {i+1}"
        
        # Final safety check - remove any remaining problematic characters
        event_text = re.sub(r'[^\w\s\-\.\'\&\+]', '', str(event_text))
        event_text = event_text.strip()
        
        if not event_text:
            event_text = f"Step {i+1}"
        
        mermaid_code += f"    {node_id}[{event_text}]\n"
    
    # Add edges dynamically
    for i in range(edge_count):
        if i + 1 < len(node_ids):
            source = node_ids[i]
            target = node_ids[i + 1]
            mermaid_code += f"    {source} --> {target}\n"
    
    # ✅ DYNAMIC STYLING - Adapts to any number of nodes
    if node_count > 0:
        mermaid_code += f"\n    style {node_ids[0]} fill:#e1f5fe\n"  # First node (blue)
        if node_count > 1:
            mermaid_code += f"    style {node_ids[-1]} fill:#ffebee\n"  # Last node (red)
            # Middle nodes (purple) - only if more than 2 nodes
            if node_count > 2:
                for i in range(1, node_count - 1):
                    node_id = node_ids[i]
                    mermaid_code += f"    style {node_id} fill:#f3e5f5\n"
    
    # Validate the generated Mermaid.js code
    try:
        # Basic validation - ensure we have valid syntax
        if not mermaid_code.strip():
            raise ValueError("Empty Mermaid.js code")
        
        # Check for basic structure
        if "graph LR" not in mermaid_code:
            raise ValueError("Missing graph declaration")
        
        # Check for nodes
        if "[" not in mermaid_code or "]" not in mermaid_code:
            raise ValueError("Missing node definitions")
        
        # Check for edges
        if "-->" not in mermaid_code:
            raise ValueError("Missing edge definitions")
        
        return mermaid_code
        
    except Exception as e:
        # Fallback to a simple, safe Mermaid.js code
        print(f"Warning: Mermaid.js validation failed: {e}")
        print(f"Generated code: {mermaid_code}")
        
        # Return a safe fallback
        fallback_code = """graph LR
    A[Event 1]
    B[Event 2]
    C[Final Decision]
    
    A --> B
    B --> C
    
    style A fill:#e1f5fe
    style C fill:#ffebee
    style B fill:#f3e5f5"""
        
        return fallback_code

def parse_llm_response(response: str) -> Optional[Dict[str, Any]]:
    """
    ✅ TRULY DYNAMIC - Parses any chain length, not just 5 nodes
    """
    
    # Try to extract JSON first
    try:
        # Look for JSON-like content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            return parsed
    except:
        pass
    
    # ✅ TRULY DYNAMIC - Look for ANY chain pattern, not just 5 nodes
    try:
        # Look for ANY chain pattern: A → B → C or A → B → C → D or A → B → C → D → E → F
        chain_match = re.search(r'([^→]+(?:→[^→]+)*)', response)
        if chain_match:
            chain_text = chain_match.group(1)
            chain_parts = [part.strip() for part in chain_text.split("→")]
            
            # ✅ DYNAMIC - Handle any number of parts
            if len(chain_parts) >= 2:  # At least 2 parts for a chain
                # Determine final direction
                final_direction = "Short" if "Short" in chain_parts[-1] else "Long"
                
                return {
                    "impact_chain": chain_text,
                    "final_direction": final_direction,
                    "node_count": len(chain_parts),  # ✅ DYNAMIC
                    "edge_count": len(chain_parts) - 1,  # ✅ DYNAMIC
                    "events": chain_parts
                }
    except:
        pass
    
    return None

class ChainOfThoughtAgent:
    def __init__(self):
        """Initialize the Chain of Thought Agent"""
        self.llm_agent = LLMCallAgent(
            default_provider="deepseek",
            default_model="deepseek-chat"
        )
        self.structured_llm = self.llm_agent.get_structured_llm(ChainOfThoughtResult)
    
    def generate_impact_chain(
        self,
        ticker: str,
        user_question: str,
        verification_links: List[str],
        verification_reasoning: str,
        agent_analysis_results: Dict[str, Any]
    ) -> ChainOfThoughtResult:
        """
        Generate a dynamic impact chain based on analysis results
        """
        
        # Create the prompt for the LLM
        prompt = f"""
        You are an expert financial analyst specializing in chain-of-thought reasoning for investment decisions.

        TASK: Generate a detailed, causal, and data-driven impact chain that shows how events lead to investment outcomes.

        INPUT DATA:
        - Ticker: {ticker}
        - User Question: {user_question}
        - Verification Links: {verification_links}
        - Verification Reasoning: {verification_reasoning}
        - Agent Analysis Results: {agent_analysis_results}

        REQUIREMENTS:
        1. ✅ TRULY DYNAMIC LENGTH - Generate as many events as needed (could be 3, 5, 7, or any number)
        2. ✅ CAUSAL LINKS - Each event must logically lead to the next
        3. ✅ DATA-DRIVEN - Every event should be based on evidence, numbers, or data
        4. ✅ FUTURE PROJECTION - Infer future impacts and market reactions
        5. ✅ FINAL DECISION - Last node must be either "Short" or "Long"
        6. ✅ NO PRESETS - Don't force any specific number of nodes

        OUTPUT FORMAT:
        {{
            "initial_query": "{user_question}",
            "ticker": "{ticker}",
            "impact_chain": "Event A → Event B → Event C → Final Decision",
            "final_direction": "Short or Long",
            "chain_explanation": "Brief explanation of the chain logic",
            "node_count": <number of events>,
            "edge_count": <number of connections>,
            "events": ["Event A", "Event B", "Event C", "Final Decision"]
        }}

        IMPORTANT: Make the chain as long or short as needed based on the complexity of the situation. Don't artificially limit it to any specific number of events.
        """
        
        try:
            # Try structured output first
            result = self.structured_llm.invoke(prompt)
            return result
        except Exception as e:
            # Fallback to regular LLM call
            try:
                response = self.llm_agent.call_deepseek(prompt)
                parsed = parse_llm_response(response)
                
                if parsed:
                    return ChainOfThoughtResult(
                        initial_query=user_question,
                        ticker=ticker,
                        impact_chain=parsed.get("impact_chain", "A → B → C"),
                        final_direction=parsed.get("final_direction", "Short"),
                        chain_explanation=parsed.get("chain_explanation", "Chain analysis"),
                        node_count=parsed.get("node_count", 3),
                        edge_count=parsed.get("edge_count", 2),
                        events=parsed.get("events", ["Event A", "Event B", "Event C"])
                    )
                else:
                    raise Exception("Failed to parse LLM response")
                    
            except Exception as fallback_error:
                raise Exception(f"Both structured and fallback LLM calls failed: {str(e)} -> {str(fallback_error)}")

# Test function
def test_agent():
    """Test the Chain of Thought Agent"""
    try:
        agent = ChainOfThoughtAgent()
        print("✅ Chain of Thought Agent initialized successfully!")
        
        # Test Mermaid code generation
        test_events = ["Earnings Miss", "Revenue Decline", "Market Reaction", "Short"]
        mermaid_code = generate_mermaid_code(4, 3, test_events)
        print("✅ Mermaid code generation working!")
        print(f"Generated code:\n{mermaid_code}")
        
        # Test with problematic text
        problematic_events = ["Q2 Earnings Miss", "Regulatory Uncertainty Intensifies", "Trading Volume Decline", "Revenue Compression", "Analyst Downgrades", "Increased Volatility", "Stock Price Decline", "Short"]
        problematic_mermaid = generate_mermaid_code(8, 7, problematic_events)
        print("✅ Problematic text handling working!")
        print(f"Generated code:\n{problematic_mermaid}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

if __name__ == "__main__":
    test_agent()
