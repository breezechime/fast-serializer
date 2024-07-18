def isinstance_safe(v, tp) -> bool:
    try:
        return isinstance(v, tp)
    except TypeError:
        return False


def test():
    return 'Hello World'