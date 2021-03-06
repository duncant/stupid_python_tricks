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

from itertools import *
from fractions import gcd
from operator import itemgetter


def simple():
    """A simple prime generator using the Sieve of Eratosthenes.

    This is not intended to be fast, but is instead intended to be so
    simple that its correctness is obvious.
    """
    stream = count(2)
    while True:
        prime = next(stream)
        sieve = (lambda n: lambda i: i % n)(prime)
        stream = ifilter(sieve, stream)
        yield prime


def take(n, stream):
    return islice(stream, None, n, None)


def drop(n, stream):
    return islice(stream, n, None, None)


def nth(n, stream):
    try:
        return next(drop(n, stream))
    except StopIteration:
        raise IndexError("Can't get element off the end of generator")



class Wheel(object):
    class Spokes(object):
        def __init__(self, iterator, length, last):
            self.iterator = take(length, iterator)
            self.length = length
            self.last = last
            self.cache = []

        def __len__(self):
            return self.length

        def __getitem__(self, key):
            cache = self.cache
            if key >= len(cache):
                try:
                    it_next = self.iterator.next
                    append = cache.append
                    while key >= len(cache):
                        append(it_next())
                except StopIteration:
                    raise IndexError("%s index out of range or iterator ended early" % type(self).__name__)
            return cache[key % self.length]

        def index(self, needle):
            left = 0
            left_value = self[left]
            right = self.length-1
            right_value = self.last
            while True:
                guess = ((right - left) * max(needle - left_value, 0) \
                         // max(right_value - left_value, 1)) + left
                guess_value = self[guess]
                if guess_value == needle:
                    # base case; needle is found
                    return guess
                elif guess_value < needle:
                    left = guess + 1
                    left_value = self[left]
                elif guess-1 < 0 or self[guess-1] < needle:
                    # base case; needle isn't present; return the
                    # index of the next-largest element
                    return guess
                else:
                    right = guess - 1
                    right_value = self[right]



    def __init__(self, smaller, prime):
        if smaller is None and prime is None:
            self.modulus = 1
            self.spokes = self.Spokes((1,), 1, 1)
        else:
            self.modulus = smaller.modulus * prime
            self.spokes = self.Spokes(ifilter(lambda x: x % prime,
                                              smaller),
                                      len(smaller.spokes)*(prime-1),
                                      self.modulus)


    def _index_unsafe(self, elem):
        cycle, raw_spoke = divmod(elem, self.modulus)
        spoke = self.spokes.index(raw_spoke)
        return (cycle, spoke)


    def index(self, elem):
        ret = self._index_unsafe(elem)
        if self[ret] != elem:
            raise IndexError("%d is not in %s" % (elem, type(self).__name__))
        return ret


    def __getitem__(self, (cycle, spoke)):
        return cycle*self.modulus + self.spokes[spoke]


    def __contains__(self, elem):
        return gcd(elem, self.modulus) == 1


    def __iter__(self):
        spokes = self.spokes
        modulus = self.modulus
        for i in count():
            for j in spokes:
                yield i*modulus + j


    def roll(self, cycles, sieve=None):
        modulus = self.modulus
        spokes = self.spokes

        # populate the sieve if it's not supplied
        if sieve is None:
            sieve = {}
            for p in takewhile(lambda p: p < modulus, simple()):
                if p in self:
                    for q in dropwhile(lambda q: q < p,
                                       takewhile(lambda q: q < modulus,
                                                 simple())):
                        hazard = p*q
                        if hazard > modulus and hazard in self:
                            sieve[hazard] = (p, None, None)
                            break

        # update the sieve for our wheel size
        to_delete = set()
        to_insert = set()
        for hazard, (prime, _, __) in sieve.iteritems():
            if hazard in self:
                cycle, spoke = self._index_unsafe(hazard // prime)
                sieve[hazard] = (prime, cycle, spoke)
            else:
                to_delete.add(hazard)
                if prime in self:
                    cycle, spoke = self._index_unsafe(hazard // prime)
                    to_insert.add((prime, cycle, spoke))
        for hazard in to_delete:
            del sieve[hazard]
        for prime, cycle, spoke in sorted(to_insert):
            hazard = prime * self[(cycle, spoke)]
            while hazard in sieve:
                spoke += 1
                cycle_incr, spoke = divmod(spoke, len(spokes))
                cycle += cycle_incr
                hazard = prime * self[(cycle, spoke)]
            sieve[hazard] = (prime, cycle, spoke)
        del to_insert
        del to_delete
        # assert len(frozenset(imap(itemgetter(0), \
        #                           sieve.itervalues()))) \
        #        == len(sieve)
        # assert all(imap(lambda hazard: hazard in self, sieve.iterkeys()))

        # perform the wheel factorization
        candidate_stream = drop(len(spokes), self)
        if cycles is not None:
            candidate_stream = take(len(spokes)*cycles, candidate_stream)

        # sieve the result
        for candidate in candidate_stream:
            if candidate in sieve:
                hazard = candidate
                prime, cycle, spoke = sieve[hazard]
                # assert hazard == prime * self[(cycle, spoke)]
                while hazard in sieve:
                    spoke += 1
                    cycle_incr, spoke = divmod(spoke, len(spokes))
                    cycle += cycle_incr
                    hazard = prime * self[(cycle, spoke)]
                # assert hazard in self
                del sieve[candidate]
                sieve[hazard] = (prime, cycle, spoke)
            else:
                cycle, spoke = self._index_unsafe(candidate)
                sieve[candidate**2] = (candidate, cycle, spoke)
                yield candidate
            # assert all(imap(lambda h: h > candidate, sieve.iterkeys()))


    class __metaclass__(type):
        def __iter__(cls):
            last = cls(None, None)
            yield last
            for prime in simple():
                last = cls(last, prime)
                yield last


    def __repr__(self):
        return "<%s.%s with modulus %d>" % \
            (__name__, type(self).__name__, self.modulus)



def fixed_wheel(index):
    w = nth(index, Wheel)
    return chain(takewhile(lambda p: p < w.modulus, simple()),
                 w.roll(None))



def variable_wheel():
    sieve = {}
    return chain.from_iterable( ( wheel.roll(prime-1, sieve)
                                  for wheel, prime in izip(Wheel, simple()) ) )



def _check_fixed(index, up_to):
    try:
        import pyprimes.sieves
        good_stream = pyprimes.sieves.best_sieve()
    except ImportError:
        good_stream = simple()
    for i, (a, b) in enumerate(take(up_to,
                                    izip(fixed_wheel(index),
                                         good_stream))):
        if a != b:
            return i

def _check_variable(up_to):
    try:
        import pyprimes.sieves
        good_stream = pyprimes.sieves.best_sieve()
    except ImportError:
        good_stream = simple()
    for i, (a, b) in enumerate(take(up_to,
                                    izip(variable_wheel(),
                                         good_stream))):
        if a != b:
            return i


if __name__ == '__main__':
    import sys
    print nth(int(sys.argv[1]), variable_wheel())
