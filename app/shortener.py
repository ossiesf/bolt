import string, random
def create_short_code(length = 6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))