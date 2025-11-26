# IVR Language Selection Flow

## Complete Flow with Retry Logic

```
┌─────────────────────────────────────────────────────────────┐
│                     📞 User Calls                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  🔊 "Welcome to Electrical Department Customer Support"    │
│  🔊 "తెలుగు కోసం 1 నొక్కండి"                              │
│  🔊 "हिंदी के लिए 2 दबाएं"                                 │
│  🔊 "Press 3 for English"                                   │
│                                                             │
│  ⏱️ Waiting 10 seconds...                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
            ✅ User Presses    ❌ No Input (Timeout)
            1, 2, or 3              │
                    │               ↓
                    │     ┌─────────────────────┐
                    │     │ 🔊 "Please select"  │
                    │     │ 🔊 "దయచేసి ఎంచుకోండి" │
                    │     │ (Retry Menu)        │
                    │     └─────────────────────┘
                    │               ↓
                    │       ⏱️ Wait 10s again
                    │               ↓
                    │     ┌─────────┴─────────┐
                    │     │                   │
                    │  ✅ Input          ❌ No Input
                    │     │                   │
                    │     │                   ↓
                    │     │         🔊 "No input received"
                    │     │         🔊 "తెలుగుకు మారుతోంది"
                    │     │         → Default to Telugu
                    │     │
                    └─────┴───────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
            ✅ Valid (1,2,3)   ❌ Invalid (4,5,6...)
                    │               │
                    │               ↓
                    │     ┌─────────────────────┐
                    │     │ 🔊 "Invalid"        │
                    │     │ 🔊 "చెల్లని ఎంపిక"    │
                    │     │ → Retry Menu        │
                    │     └─────────────────────┘
                    │               ↓
                    │       ⏱️ Wait 10s again
                    │               ↓
                    │     ┌─────────┴─────────┐
                    │     │                   │
                    │  ✅ Valid          ❌ Invalid Again
                    │     │                   │
                    │     │                   ↓
                    │     │         → Default to Telugu
                    │     │
                    └─────┴───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              ✅ Language Confirmed                          │
│                                                             │
│  Telugu:  🔊 "తెలుగు. మీకు ఎలా సహాయం చేయగలను?"            │
│  Hindi:   🔊 "हिंदी। मैं आपकी कैसे मदद कर सकता हूं?"       │
│  English: 🔊 "English. How may I assist you?"              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           🔌 Connect to AI Voice Agent                      │
│           (WebSocket with selected language)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Scenarios

### ✅ **Scenario 1: User Presses 1 Immediately**
```
Call → Menu → Press 1 → "తెలుగు. మీకు ఎలా సహాయం చేయగలను?" → Conversation
Time: ~5 seconds
```

### ✅ **Scenario 2: User Doesn't Press Anything (First Time)**
```
Call → Menu → Wait 10s → "Please select" → Menu Again → Press 1 → Conversation
Time: ~15 seconds
```

### ✅ **Scenario 3: User Doesn't Press Anything (Second Time)**
```
Call → Menu → Wait 10s → Retry Menu → Wait 10s → "తెలుగుకు మారుతోంది" → Telugu
Time: ~20 seconds
```

### ✅ **Scenario 4: User Presses Invalid Key (First Time)**
```
Call → Menu → Press 5 → "Invalid" → Menu Again → Press 1 → Conversation
Time: ~10 seconds
```

### ✅ **Scenario 5: User Presses Invalid Key (Second Time)**
```
Call → Menu → Press 5 → "Invalid" → Menu Again → Press 9 → Default Telugu
Time: ~15 seconds
```

---

## Benefits

### ✅ **User-Friendly**
- Gives second chance for mistakes
- Clear error messages
- Doesn't hang up on user

### ✅ **Professional**
- Standard IVR behavior
- Multilingual error messages
- Graceful fallback to Telugu

### ✅ **Robust**
- Handles all edge cases
- Never gets stuck
- Always proceeds to conversation

---

## Implementation Details

### **Retry Counter**
```python
retry = "0"  # First attempt
retry = "1"  # Second attempt (after timeout/invalid)
```

### **Timeout Handling**
```python
# First timeout → Ask again
if retry == "0":
    response.redirect('/voice/incoming?retry=1')

# Second timeout → Default to Telugu
if retry == "1":
    response.redirect('/voice/language-selected?Digits=1')
```

### **Invalid Input Handling**
```python
# First invalid → Ask again
if digit not in language_map and retry == "0":
    response.say("Invalid selection")
    response.redirect('/voice/incoming?retry=1')

# Second invalid → Default to Telugu
if digit not in language_map and retry == "1":
    digit = "1"  # Telugu
```

---

## Real-World IVR Behavior ✅

This matches how professional IVR systems work:
- ✅ Amazon customer service
- ✅ Bank helplines
- ✅ Airline booking systems
- ✅ Government services

**Your AI agent now behaves like a real-world professional IVR!** 🎉
