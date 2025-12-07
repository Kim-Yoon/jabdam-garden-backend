def validate_password_strength(v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError('소문자를 최소 1개 포함해야 합니다')
        if not any(c.isupper() for c in v):
            raise ValueError('대문자를 최소 1개 포함해야 합니다')
        if not any(c.isdigit() for c in v):
            raise ValueError('숫자를 최소 1개 포함해야 합니다')
        if not any(c in '!@#$%^&*' for c in v):
            raise ValueError('특수문자(!@#$%^&*)를 최소 1개 포함해야 합니다')
        return v

def check_passwords_match(password: str, password_confirm: str) -> bool:
    """두 비밀번호가 일치하는지 검증"""
    if password != password_confirm:
        raise ValueError('비밀번호가 일치하지 않습니다')