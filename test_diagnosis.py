# test_diagnosis.py
"""Diagnose what's wrong"""

print("\n" + "="*80)
print("🔍 AURA DIAGNOSIS")
print("="*80)

# Step 1: Check imports
print("\n📦 Step 1: Checking imports...")
try:
    from aura import get_engine
    print("✅ from aura import get_engine - OK")
except Exception as e:
    print(f"❌ from aura import get_engine - FAILED: {e}")
    import sys
    sys.exit(1)

# Step 2: Get engine
print("\n⚙️ Step 2: Getting engine...")
try:
    engine = get_engine()
    print("✅ engine = get_engine() - OK")
except Exception as e:
    print(f"❌ engine = get_engine() - FAILED: {e}")
    import traceback
    traceback.print_exc()
    import sys
    sys.exit(1)

# Step 3: Check handlers
print("\n📋 Step 3: Checking handlers...")
print(f"   Handlers registered: {len(engine.handlers)}")
for name in engine.handlers:
    handler = engine.handlers[name]
    print(f"   ✅ {name}: keywords={handler.keywords}")

if len(engine.handlers) == 0:
    print("   ❌ NO HANDLERS REGISTERED!")
    import sys
    sys.exit(1)

# Step 4: Test matching
print("\n🧪 Step 4: Testing command matching...")
test_cases = [
    "open chrome",
    "play music",
    "search for python",
]

for cmd in test_cases:
    match = engine.find_best_match(cmd, min_confidence=0.1)
    if match:
        print(f"   ✅ '{cmd}' → {match.handler_name} (conf: {match.confidence:.2f})")
    else:
        print(f"   ❌ '{cmd}' → NO MATCH")

print("\n" + "="*80)
