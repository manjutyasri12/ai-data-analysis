"""
Test Conversation Memory
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_data_project.settings')
django.setup()

from dataapp.services.ai_assistant import (
    save_conversation_message,
    get_conversation_history,
    clear_conversation_history,
)
from dataapp.models import ConversationHistory


def test_save_conversation_message():
    print("\n[TEST 1] Save Conversation Message")

    ConversationHistory.objects.filter(session_id="test_session").delete()

    save_conversation_message("test_session", "user", "What is the data?")
    save_conversation_message("test_session", "assistant", "The data has 100 rows...")

    messages = ConversationHistory.objects.filter(session_id="test_session").count()
    assert messages == 2

    print("[PASS] Save conversation test")
    return True


def test_retrieve_conversation_history():
    print("\n[TEST 2] Retrieve Conversation History")

    session_id = "test_session_2"
    ConversationHistory.objects.filter(session_id=session_id).delete()

    for i in range(5):
        save_conversation_message(
            session_id,
            "user" if i % 2 == 0 else "assistant",
            f"Test message {i}",
        )

    history = get_conversation_history(session_id, limit=10)
    assert len(history) == 5
    assert all('message' in msg for msg in history)
    assert all('role' in msg for msg in history)
    assert all('created_at' in msg for msg in history)

    print("[PASS] Retrieve history")
    return True


def test_clear_conversation_history():
    print("\n[TEST 3] Clear Conversation History")

    session_id = "test_session_4"

    for i in range(3):
        save_conversation_message(session_id, "user", f"Message {i}")

    before = ConversationHistory.objects.filter(session_id=session_id).count()
    assert before == 3

    cleared = clear_conversation_history(session_id)
    assert cleared is True

    after = ConversationHistory.objects.filter(session_id=session_id).count()
    assert after == 0

    print("[PASS] Clear history")
    return True


if __name__ == '__main__':
    print("=" * 50)
    print("CONVERSATION MEMORY TESTS")
    print("=" * 50)

    results = []
    results.append(("Save Message", test_save_conversation_message()))
    results.append(("Retrieve History", test_retrieve_conversation_history()))
    results.append(("Clear History", test_clear_conversation_history()))

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

