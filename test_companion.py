"""
Quick smoke-test for the companion agent.
Run from the pulse/ directory:

    .venv/bin/python test_companion.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

INPUTS = [
    "I feel a bit dizzy today.",
    "I haven't taken my pills for a week.",
    "I have a question about my medications.",
    "I didn't sleep well, maybe 4 hours.",
    "I'm feeling good today!",
]

def run():
    from graph.workflow import get_graph
    from graph.state import initial_state

    graph = get_graph()

    for msg in INPUTS:
        print(f"\n{'='*60}")
        print(f"USER: {msg}")
        print("-"*60)
        try:
            result = graph.invoke(initial_state(msg))
            reply  = result.get("companion_response", "")
            entry  = result.get("new_entry", {})
            print(f"PULSE: {reply}")
            print(f"  → logged: symptoms={entry.get('symptoms')}, "
                  f"severity={entry.get('severity')}, sleep={entry.get('sleep_hours')}")
            print(f"  → route_to_analyst={result.get('route_to_analyst')}")
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run()
