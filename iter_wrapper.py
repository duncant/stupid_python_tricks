# This file is part of stupid_python_tricks written by Duncan Townsend.
#
# stupid_python_tricks is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# stupid_python_tricks is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with stupid_python_tricks.  If not, see <http://www.gnu.org/licenses/>.


from collections import deque, Iterator, Iterable
from proxy import BetterProxy

class IterWrapper(BetterProxy):
    """This class adds a bunch of useful functionality to iterators.

    Subscript notation [] "peeks" ahead in the iterator. If you "peek" a value,
    it will still be returned by the ".next()" method as usual. If the iterator
    has terminated before reaching the value you want to "peek", the subscript
    operation will raise an IndexError.
    
    The "drop" method immediately advances the iterator the given number of
    items forward, ignoring the values returned. Attempting to drop 0 items does
    nothing. Attempting to drop more items than the iterator has will raise an
    IndexError.

    The "push" method adds an arbitrary value to the beginning of the
    iterator. That is, the next value peeked or returned by ".next()" will be
    the value supplied to the "push" method.  It is possible to use the push
    method to "restart" a finished iterator. If the underlying iterator has
    previously raised a StopIteration exception, pushing a new value onto the
    iterator will cause the next invocation of the ".next()" method to return
    the pushed item.

    All other methods of the iterator are mirrored unmodified.
    """
    @classmethod
    def _ensure_iterator(cls, obj):
        if not isinstance(obj, Iterable):
            raise TypeError("Can only wrap Iterable objects")
        elif not isinstance(obj, Iterator):
            return cls._ensure_iterator(iter(obj))
        else:
            return obj

    def __new__(cls, obj):
        return super(IterWrapper, cls).__new__(cls, cls._ensure_iterator(obj))

    def __init__(self, obj):
        super(IterWrapper, self).__init__(self._ensure_iterator(obj))
        assert isinstance(self._obj, type(self))
        object.__setattr__(self, '_cache', deque())

    def __iter__(self):
        return self

    def next(self):
        if len(self._cache) == 0:
            return next(self._obj)
        else:
            return self._cache.popleft()

    def drop(self,count):
        if count == 0:
            return
        self[count-1] # ensure we have at least this many 
        for i in xrange(count):
            self._cache.popleft()

    def push(self,item):
        self._cache.appendleft(item)

    def __getitem__(self,index):
        if isinstance(index,slice):
            start, stop, step = index.start, index.stop, index.step

            if start is None:
                start = 0
            elif start < 0:
                raise IndexError("Can't peek from the end of the iterator")
                
            if step is None:
                step = 1
            elif step < 0:
                raise IndexError("Can't peek from the end of the iterator")
                
            if stop is None:
                self._cache.extend(self._obj)
                return list(self._cache[start::step])
            elif stop < 0:
                raise IndexError("Can't peek from the end of the iterator")
            else:
                try:
                    for i in xrange(len(self._cache),stop):
                        self._cache.append(self._obj.next())
                except StopIteration:
                    pass
                return list(self._cache[start:stop:step])
        else:
            if index < 0:
                raise IndexError("Can't peek from the end of the iterator")
            else:
                if len(self._cache) > index:
                    return self._cache[index]
                else:
                    try:
                        for i in xrange(index+1-len(self._cache)):
                            self._cache.append(self._obj.next())
                        return self._cache[index]
                    except StopIteration:
                        raise IndexError("Peek index out of range")
