
#!/usr/bin/env python3
"""
Test script for OpenRouter integration and AI Engineer system
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assistant.openrouter_client import OpenRouterFree
from assistant.core import AIEngineer

async def test_openrouter_client():
    """Test OpenRouter client functionality"""
    print("🧪 Testing OpenRouter Client...")
    
    # Test configuration
    config = {
        'api_key': os.getenv('OPENROUTER_API_KEY'),
        'app_name': 'Quantum-Loop-Debugger-Test',
        'app_url': 'https://github.com/zebadiee/quantum-loop-debugger'
    }
    
    if not config['api_key']:
        print("⚠️  OPENROUTER_API_KEY not set, skipping OpenRouter tests")
        return False
    
    try:
        # Initialize client
        client = OpenRouterFree(config)
        print(f"✅ Client initialized with model: {client.current_model}")
        
        # Test health check
        health = await client.health_check()
        print(f"🏥 Health check: {health['status']}")
        print(f"📊 Available models: {health.get('available_models_count', 0)}/{health.get('total_models', 0)}")
        
        # Test model listing
        models = client.list_available_models()
        available_count = sum(1 for model in models.values() if model['available'])
        print(f"🔄 Available models for rotation: {available_count}")
        
        # Test usage summary
        usage = client.get_usage_summary()
        print(f"📈 Usage summary: {len(usage)} models tracked")
        
        # Test simple query (if models available)
        if available_count > 0:
            print("💬 Testing simple query...")
            response = await client.query("Hello! Can you respond with 'AI Engineer Test Successful'?")
            print(f"🤖 Response: {response[:100]}...")
            
            # Test model rotation
            if available_count > 1:
                print("🔄 Testing model rotation...")
                old_model = client.current_model
                success = client.force_model_rotation()
                if success:
                    print(f"✅ Rotation successful: {old_model} → {client.current_model}")
                else:
                    print("⚠️  No models available for rotation")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False

async def test_ai_engineer():
    """Test AI Engineer core functionality"""
    print("\n🧪 Testing AI Engineer Core...")
    
    try:
        # Initialize AI Engineer
        ai_engineer = AIEngineer()
        print("✅ AI Engineer initialized")
        
        # Test system health
        health_request = {'type': 'system_health'}
        health_response = await ai_engineer.handle_request(health_request)
        
        if health_response.get('success'):
            print("🏥 System health check passed")
            health_data = health_response.get('health', {})
            print(f"   AI Engineer: {health_data.get('ai_engineer', 'unknown')}")
            print(f"   OpenRouter: {health_data.get('openrouter', {}).get('status', 'unknown')}")
            print(f"   Git: {health_data.get('git', {}).get('status', 'unknown')}")
        else:
            print(f"❌ Health check failed: {health_response.get('error')}")
        
        # Test OpenRouter status
        or_request = {'type': 'openrouter_status'}
        or_response = await ai_engineer.handle_request(or_request)
        
        if or_response.get('success'):
            print("🔄 OpenRouter status check passed")
            print(f"   Current model: {or_response.get('current_model', 'none')}")
            print(f"   Available models: {len([m for m in or_response.get('available_models', {}).values() if m.get('available')])}")
        else:
            print(f"❌ OpenRouter status failed: {or_response.get('error')}")
        
        # Test LLM query (if OpenRouter is configured)
        if os.getenv('OPENROUTER_API_KEY'):
            print("💬 Testing LLM query...")
            llm_request = {
                'type': 'llm_query',
                'query': 'Respond with exactly: "AI Engineer integration test successful"'
            }
            llm_response = await ai_engineer.handle_request(llm_request)
            
            if llm_response.get('success'):
                response_text = llm_response.get('response', '')
                print(f"🤖 LLM Response: {response_text[:100]}...")
                print(f"   Model used: {llm_response.get('model_used', 'unknown')}")
            else:
                print(f"❌ LLM query failed: {llm_response.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Engineer test failed: {e}")
        return False

def test_configuration():
    """Test system configuration"""
    print("🧪 Testing Configuration...")
    
    # Check required files
    required_files = [
        'assistant/core.py',
        'assistant/openrouter_client.py',
        'assistant/git_integration.py',
        'assistant/tools/mcp_client.py',
        'tk_dashboard.py',
        'tk_patch_generator.py',
        'tk_auto_retry.py',
        'docker-compose.yml',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
    
    # Check environment variables
    env_vars = ['OPENROUTER_API_KEY', 'GITHUB_TOKEN', 'WORKSPACE_PATH']
    missing_env = []
    for var in env_vars:
        if not os.getenv(var):
            missing_env.append(var)
    
    if missing_env:
        print(f"⚠️  Missing environment variables: {missing_env}")
        print("   Set these in .env file or environment")
    else:
        print("✅ All environment variables configured")
    
    return len(missing_files) == 0

async def main():
    """Main test runner"""
    print("=" * 60)
    print("🚀 QUANTUM LOOP DEBUGGER - INTEGRATION TESTS")
    print("=" * 60)
    print(f"📅 Test run: {datetime.now().isoformat()}")
    print()
    
    # Load environment from .env file if it exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📁 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print()
    
    # Run tests
    tests = [
        ("Configuration", test_configuration),
        ("OpenRouter Client", test_openrouter_client),
        ("AI Engineer Core", test_ai_engineer)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
