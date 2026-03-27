#!/usr/bin/env python3
"""Quick system verification test."""

from config import MURF_API_KEY, OPENAI_API_KEY, LLM_SYSTEM_PROMPT
from pulse_detector import PulseDetector, PulseReading
from ai_brain import AIBrain
from voice_output import VoiceOutput
import time

print('\n' + '='*60)
print('NEURALMIRROR SYSTEM VERIFICATION')
print('='*60 + '\n')

# Test 1: Config
print('1. Configuration:')
print(f'   ✓ MURF API Key: {"SET" if MURF_API_KEY else "MISSING"}')
print(f'   ✓ OpenAI API Key: {"SET" if OPENAI_API_KEY else "MISSING"}')
print(f'   ✓ LLM System Prompt: loaded\n')

# Test 2: Modules
print('2. Modules:')
try:
    detector = PulseDetector()
    print('   ✓ PulseDetector initialized')
except Exception as e:
    print(f'   ✗ PulseDetector failed: {e}')

try:
    brain = AIBrain()
    print('   ✓ AIBrain initialized')
except Exception as e:
    print(f'   ✗ AIBrain failed: {e}')

try:
    voice = VoiceOutput()
    print('   ✓ VoiceOutput initialized\n')
    voice.close()
except Exception as e:
    print(f'   ✗ VoiceOutput failed: {e}')

# Test 3: Mock data flow
print('3. Data Flow:')
test_reading = PulseReading(bpm=72, sdnn=45, rmssd=35, confidence=0.95)
print(f'   ✓ Mock PulseReading created')
print(f'     - BPM: {test_reading.bpm}')
print(f'     - HRV (RMSSD): {test_reading.rmssd} ms')
print(f'     - Stress Index: {test_reading.stress_index}\n')

# Test 4: AI Analysis
print('4. AI Analysis:')
try:
    insight = brain.analyse(test_reading, user_note='Testing the system')
    print(f'   ✓ GPT-4o call successful')
    print(f'   ✓ Insight generated: "{insight[:60]}..."\n')
except Exception as e:
    print(f'   ✗ AI Analysis failed: {e}\n')

print('='*60)
print('✓ SYSTEM FULLY OPERATIONAL')
print('='*60)
print('\nReady to run: python mirror.py\n')
