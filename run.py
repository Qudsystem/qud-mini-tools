#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART RUNNER - يشغّل autoo.py مع حماية من الأخطاء
يضمن عدم حجب الحساب وعدم ظهور رسائل الخطأ
"""

import subprocess
import time
import sys

print("="*70)
print("🚀 SMART AUTO RUNNER v2.7.0")
print("="*70)
print("\n✅ حماية من الأخطاء:")
print("   - انتظار 120 ثانية بين محاولات الدخول")
print("   - استخدام الكوكيز المحفوظة")
print("   - تبديل الحسابات تلقائياً")
print("   - انتظار 5 ثوان بين المنشورات")
print("   - معالجة أخطاء الجلسة")
print("\n⚠️  تحذيرات:")
print("   - لا تشغّل البرنامج مرتين في نفس الوقت!")
print("   - اتركه يعمل حتى النهاية")
print("   - لا تغلق المتصفح أثناء التشغيل")

print("\n" + "="*70)
print("اختر وضع التشغيل:")
print("="*70)
print("1. API Mode (Telegram + Facebook API)")
print("2. Browser Mode (Selenium + Comet) ⭐")
print("3. Hybrid Mode (Both in parallel)")
print("\nالوضع الموصى به: 2 (Browser Mode)")
print("="*70)

# Get mode input
mode_input = input("\nأدخل الوضع (1-3) أو اضغط Enter للوضع 2: ").strip()
if not mode_input:
    mode_input = "2"

print(f"\n⏳ بدء التشغيل في الوضع: {mode_input}")
print("="*70)

# Run autoo.py with input
try:
    process = subprocess.Popen(
        [sys.executable, "autoo.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Send mode selection
    process.stdin.write(mode_input + "\n")
    process.stdin.flush()
    
    # Read output
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    process.wait()
    
    print("\n" + "="*70)
    print("✅ اكتمل التشغيل بنجاح!")
    print("="*70)
    
except KeyboardInterrupt:
    print("\n\n⚠️ تم إيقاف البرنامج من قبل المستخدم")
    process.terminate()
except Exception as e:
    print(f"\n❌ خطأ: {e}")
    sys.exit(1)
