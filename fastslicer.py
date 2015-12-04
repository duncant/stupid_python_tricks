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


from numbers import Integral
from itertools import islice
from sys import maxint

from proxy import BetterProxy

class FastSlicer(BetterProxy):
    def __new__(cls, obj, start=None, stop=None, *args, **kwargs):
        return super(FastSlicer, cls).__new__(cls, obj, *args, **kwargs)

    def __init__(self, obj, start=None, stop=None):
        super(FastSlicer, self).__init__(obj)
        if isinstance(obj, FastSlicer):
            obj._check_bounds(obj._get_concrete(start, default=0),
                              obj._get_concrete(stop, default=len(obj)))

            self._obj = obj._obj
            if start is None:
                start = obj.start
            else:
                if start < 0:
                    start += obj.stop
                else:
                    start += obj.start

            if stop is None:
                stop = obj.stop
            else:
                if stop < 0:
                    stop += obj.stop
                else:
                    stop += obj.start

        object.__setattr__(self, 'start', start)
        object.__setattr__(self, 'stop', stop)

    def _get_concrete(self, index, default=None):
        if index is None:
            if default is None:
                return None
            else:
                index = default

        if index < 0:
            if self.stop is None:
                index += len(self._obj)
            elif self.stop < 0:
                index += len(self._obj) + self.stop
            else:
                index += self.stop
        elif self.start is not None:
            index += self.start

        return index

    def _check_index(self, index):
        if ( self.start is not None and index < self.start ) \
           or index < 0 \
           or ( self.stop is not None and index >= self.stop ) \
           or index >= len(self._obj):
            raise IndexError('Index outside slice bounds')

    def _check_bounds(self, start, stop):
        self._check_index(start)
        self._check_index(stop-1)
        if stop < start:
            raise IndexError('Bad range')

    def __len__(self):
        return self.stop - self.start

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            return type(self)(self._obj, start=start, stop=stop)
        elif isinstance(key, Integral):
            key = self._get_concrete(key, default=0)
            self._check_index(key)
            return self._obj[key]
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            start = self._get_concrete(key.start, default=0)
            stop = self._get_concrete(key.stop, default=len(self))
            self._check_bounds(start, stop)
            try:
                if len(value) != stop-start:
                    raise TypeError
            except TypeError:
                import warnings
                warnings.warn('Changing the length of a FastSlicer instance may have unexpected results')
            self._obj[start:stop] = value
        elif isinstance(key, Integral):
            key = self._get_concrete(key, default=0)
            self._check_index(key)
            self._obj[key] = value
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __delitem__(self, key):
        import warnings
        warnings.warn('Deleting elements of a FastSlicer instance may have unexpected results')
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise NotImplementedError('FastSlicer objects do not support step slices')
            start = self._get_concrete(key.start, default=0)
            stop = self._get_concrete(key.stop, default=len(self))
            self._check_bounds(start, stop)
            del self._obj[start:stop]
        elif isinstance(key, Integral):
            key = self._get_concrete(key, default=0)
            self._check_index(key)
            del self._obj[key]
        else:
            raise TypeError('Cannot use objects of type %s as indexes' % type(key).__name__)

    def __str__(self):
        return str(self._obj[self.start:self.stop])

    def __iter__(self):
        return islice(self._obj, self.start, self.stop)

    def __bool__(self):
        return len(self) > 0
