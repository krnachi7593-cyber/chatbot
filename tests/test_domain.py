from app.assistant import detect_budget, detect_category, policy_answer

def test_detect_budget():
    assert detect_budget("headphones under ₹3,000") == 3000

def test_detect_category():
    assert detect_category("recommend a laptop") == "Electronics"

def test_policy_answer():
    assert policy_answer("What is your return policy?")[0][0] == "returns"
