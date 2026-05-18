#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.core.security import get_password_hash, verify_password

password = "111111"
hashed = get_password_hash(password)

print(f"原始密码: {password}")
print(f"加密后:   {hashed}")
print(f"验证结果: {verify_password(password, hashed)}")
