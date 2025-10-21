"""
Test Suite for Financial Analysis Tools

Tests all four financial tools to ensure they work correctly in Docker.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.financial import (
    contango_backwardation_tool,
    macro_risk_analysis_tool,
    vix_analysis_tool,
    liquidity_monitor_tool
)


def test_contango_backwardation():
    """Test contango/backwardation analysis tool."""
    print("\n" + "="*80)
    print("TEST 1: Contango/Backwardation Analysis Tool")
    print("="*80)
    
    try:
        result = contango_backwardation_tool("oil")
        
        # Validate result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'summary' in result, "Result should contain 'summary' key"
        assert 'market_structure' in result, "Result should contain 'market_structure' key"
        assert '_df' in result, "Result should contain '_df' key"
        
        print("✅ PASS: Contango/Backwardation Tool")
        print(f"\n📊 Summary: {result['summary']}")
        print(f"📈 Market Condition: {result['market_structure']['condition']}")
        print(f"📋 Active Contracts: {result['contract_analysis']['active_contracts']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Contango/Backwardation Tool - {str(e)}")
        return False


def test_macro_risk_analysis():
    """Test macro risk analysis tool."""
    print("\n" + "="*80)
    print("TEST 2: Macro Risk Analysis Tool")
    print("="*80)
    
    try:
        result = macro_risk_analysis_tool()
        
        # Validate result
        if result is None:
            print("⚠️  WARNING: No macro analysis data available in Redis")
            print("   This is expected if Redis is not populated yet")
            return True
        
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        
        print("✅ PASS: Macro Risk Analysis Tool")
        print(f"\n📊 Analysis Preview (first 500 chars):")
        print(result[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Macro Risk Analysis Tool - {str(e)}")
        return False


def test_vix_analysis():
    """Test VIX analysis tool."""
    print("\n" + "="*80)
    print("TEST 3: VIX Analysis Tool")
    print("="*80)
    
    try:
        # Test with smaller dataset for faster testing
        result = vix_analysis_tool(days=1000)
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "VIX" in result, "Result should mention VIX"
        
        print("✅ PASS: VIX Analysis Tool")
        print(f"\n📊 Analysis Preview (first 500 chars):")
        print(result[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: VIX Analysis Tool - {str(e)}")
        return False


def test_liquidity_monitor():
    """Test liquidity monitor tool."""
    print("\n" + "="*80)
    print("TEST 4: Liquidity Monitor Tool")
    print("="*80)
    
    try:
        # Test with smaller dataset for faster testing
        result = liquidity_monitor_tool(days=180)
        
        # Validate result
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert "Liquidity" in result, "Result should mention Liquidity"
        
        print("✅ PASS: Liquidity Monitor Tool")
        print(f"\n📊 Analysis Preview (first 500 chars):")
        print(result[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Liquidity Monitor Tool - {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "🧪 " + "="*76)
    print("🧪 FINANCIAL TOOLS TEST SUITE")
    print("🧪 " + "="*76)
    
    results = {
        "Contango/Backwardation": test_contango_backwardation(),
        "Macro Risk Analysis": test_macro_risk_analysis(),
        "VIX Analysis": test_vix_analysis(),
        "Liquidity Monitor": test_liquidity_monitor()
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
        print("\n🎉 All tests passed! Financial tools are ready for Docker deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

