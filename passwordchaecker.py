def password_checker(password):
    special_chars = "!@#$%^&*()-_=+[]{}|;:',.<>?/~`"
    if len(password) < 8: 
        return "Password too short (min 8 chars)."
    if not password[0].isupper(): 
        return "First char must be uppercase."
    has_digit = has_special = has_lower = False
    for ch in password:
        if ch.isdigit(): has_digit = True
        elif ch.islower(): has_lower = True
        elif ch in special_chars: has_special = True
        elif ch.isspace(): return "Password cannot contain spaces."
    if not has_lower: return "Password must contain lowercase letter."
    if not has_digit: return "Password must contain number."
    if not has_special: return "Password must contain special character."
    return "Password is strong ✅"
print(password_checker('Ashok8601@') )   