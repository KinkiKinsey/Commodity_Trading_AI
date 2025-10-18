"""
Test Suite for LangChain Financial Tools

Tests all four financial tools exposed as LangChain tools.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.financial import (
    contango_backwardation_analysis,
    macro_risk_analysis,
    vix_volatility_analysis,
    global_liquidity_monitor
)


def test_langchain_tool_attributes():
    """Test that tools have proper LangChain attributes."""
    print("\n" + "="*80)
    print("TEST 0: LangChain Tool Attributes")
    print("="*80)
    
    tools = [
        contango_backwardation_analysis,
        macro_risk_analysis,
        vix_volatility_analysis,
        global_liquidity_monitor
    ]
    
    for tool in tools:
        assert hasattr(tool, 'name'), f"{tool} missing 'name' attribute"
        assert hasattr(tool, 'description'), f"{tool} missing 'description' attribute"
        assert hasattr(tool, 'invoke'), f"{tool} missing 'invoke' method"
        print(f"✅ {tool.name}: Has required LangChain attributes")
    
    print("\n✅ PASS: All tools have proper LangChain attributes")
    return True


def test_contango_backwardation_langchain():
    """Test contango/backwardation LangChain tool."""
    print("\n" + "="*80)
    print("TEST 1: Contango/Backwardation LangChain Tool")
    print("="*80)
    
    try:
        # Test tool invocation
        result = contango_backwardation_analysis.invoke({"sector": "oil"})
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "Contango" in result or "Backwardation" in result, "Result should mention market structure"
        
        print("✅ PASS: Contango/Backwardation LangChain Tool")
        print(f"\n📊 Tool Name: {contango_backwardation_analysis.name}")
        print(f"📊 Result Preview (first 300 chars):")
        print(result[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Contango/Backwardation LangChain Tool - {str(e)}")
        return False


def test_macro_risk_langchain():
    """Test macro risk LangChain tool."""
    print("\n" + "="*80)
    print("TEST 2: Macro Risk LangChain Tool")
    print("="*80)
    
    try:
        # Test tool invocation
        result = macro_risk_analysis.invoke({})
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        
        print("✅ PASS: Macro Risk LangChain Tool")
        print(f"\n📊 Tool Name: {macro_risk_analysis.name}")
        print(f"📊 Result Preview (first 300 chars):")
        print(result[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Macro Risk LangChain Tool - {str(e)}")
        return False


def test_vix_langchain():
    """Test VIX LangChain tool."""
    print("\n" + "="*80)
    print("TEST 3: VIX LangChain Tool")
    print("="*80)
    
    try:
        # Test tool invocation with smaller dataset
        result = vix_volatility_analysis.invoke({"days": 1000})
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "VIX" in result, "Result should mention VIX"
        
        print("✅ PASS: VIX LangChain Tool")
        print(f"\n📊 Tool Name: {vix_volatility_analysis.name}")
        print(f"📊 Result Preview (first 300 chars):")
        print(result[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: VIX LangChain Tool - {str(e)}")
        return False


def test_liquidity_langchain():
    """Test liquidity monitor LangChain tool."""
    print("\n" + "="*80)
    print("TEST 4: Liquidity Monitor LangChain Tool")
    print("="*80)
    
    try:
        # Test tool invocation
        result = global_liquidity_monitor.invoke({"days": 180})
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "Liquidity" in result, "Result should mention Liquidity"
        
        print("✅ PASS: Liquidity Monitor LangChain Tool")
        print(f"\n📊 Tool Name: {global_liquidity_monitor.name}")
        print(f"📊 Result Preview (first 300 chars):")
        print(result[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Liquidity Monitor LangChain Tool - {str(e)}")
        return False


def main():
    """Run all LangChain tool tests."""
    print("\n" + "🧪 " + "="*76)
    print("🧪 LANGCHAIN FINANCIAL TOOLS TEST SUITE")
    print("🧪 " + "="*76)
    
    results = {
        "Tool Attributes": test_langchain_tool_attributes(),
        "Contango/Backwardation": test_contango_backwardation_langchain(),
        "Macro Risk Analysis": test_macro_risk_langchain(),
        "VIX Analysis": test_vix_langchain(),
        "Liquidity Monitor": test_liquidity_langchain()
    }
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"🎯 RESULTS: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All LangChain tools ready for LangGraph integration!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

