import decorator
import warnings
from weakref import WeakKeyDictionary
from weakcompoundkey import WeakCompoundKey

def decorator_apply(dec, func):
    """
    Decorate a function by preserving the signature even if dec
    is not a signature-preserving decorator.
    """
    return decorator.FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec(func)), __wrapped__=func)

@decorator.decorator
def decorator_decorator(dec, func):
    """Decorator for decorators"""
    return decorator_apply(dec, func)

@decorator_decorator
def memoize(f):
    cache = {}
    def memoized(*args, **kwargs):
        try:
            hash(args)
            key = (args, frozenset(kwargs.iteritems()))
            hashable = True
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) and e.args[0].startswith("unhashable type:"):
                hashable = False
            else:
                raise

        if hashable:
            if key in cache:
                return cache[key]
            else:
                cache[key] = retval = f(*args, **kwargs)
                return retval
        else:
            warnings.warn("Unable to memoize: unhashable argument")
            return f(*args, **kwargs)
    return memoized

@decorator_decorator
def weakmemoize(f):
    cache = WeakKeyDictionary()
    def weakmemoized(*args, **kwargs):
        try:
            key = WeakCompoundKey(*args, **kwargs)
            hashable = True
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) \
               and (e.args[0].startswith("unhashable type:") \
                    or e.args[0].startswith('cannot create weak reference to')):
                hashable = False
            else:
                raise

        if hashable:
            if key in cache:
                return cache[key]
            else:
                cache[key] = retval = f(*args, **kwargs)
                return retval
        else:
            warnings.warn("Unable to memoize: unable to hash or weak reference argument")
            return f(*args, **kwargs)
    return weakmemoized

memoized = memoize
weakmemoized = weakmemoize
__all__ = ['memoize','memoized', 'weakmemoize', 'weakmemoized']
