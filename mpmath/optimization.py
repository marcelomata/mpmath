# -*- encoding: utf-8 -*-

from mptypes import convert_lossless, extraprec, eps
from calculus import diff
from functions import sqrt, sign

##############
# 1D-SOLVERS #
##############

class Secant:
    """
    1d-solver generating pairs of approximative root and error.

    Needs starting points x0 and x1 close to the root.
    x1 defaults to x0 + 0.25.

    Pro:
    * converges fast
    Contra:
    * converges slowly for multiple roots
    """
    maxsteps = 30

    def __init__(self, f, x0, **kwargs):
        if len(x0) == 1:
            self.x0 = x0[0]
            self.x1 = self.x0 + 0.25
        elif len(x0) == 2:
            self.x0 = x0[0]
            self.x1 = x0[1]
        else:
            raise ValueError('expected 1 or 2 starting points, got %i' * len(x0))
        self.f = f

    def __iter__(self):
        f = self.f
        x0 = self.x0
        x1 = self.x1
        f0 = f(x0)
        while True:
            f1 = f(x1)
            l = x1 - x0
            if not l:
                break
            s = (f1 - f0) / l
            if not s:
                break
            x0, x1 = x1, x1 - f1/s
            f0 = f1
            yield x1, abs(l)

class MNewton:
    """
    1d-solver generating pairs of approximative root and error.

    Needs starting point x0 close to the root.
    Uses modified Newton's method that converges fast regardless of the
    multiplicity of the root.

    Pro:
    * converges fast for multiple roots
    Contra:
    * needs first and second derivative of f
    * 3 function evaluations per iteration
    """
    maxsteps = 20

    def __init__(self, f, x0, **kwargs):
        if not len(x0) == 1:
            raise ValueError('expected 1 starting point, got %i' * len(x0))
        self.x0 = x0[0]
        self.f = f
        if not 'df' in kwargs:
            def df(x):
                return diff(f, x)
        else:
            df = kwargs['df']
        self.df = df
        if not 'd2f' in kwargs:
            def d2f(x):
                return diff(df, x)
        else:
            d2f = kwargs['df']
        self.d2f = d2f

    def __iter__(self):
        x = self.x0
        f = self.f
        df = self.df
        d2f = self.d2f
        while True:
            prevx = x
            fx = f(x)
            if fx == 0:
		break
            dfx = df(x)
            d2fx = d2f(x)
            # x = x - F(x)/F'(x) with F(x) = f(x)/f'(x)
            x -= fx / (dfx - fx * d2fx / dfx)
            error = abs(x - prevx)
            yield x, error

class Halley:
    """
    1d-solver generating pairs of approximative root and error.

    Needs a starting point x0 close to the root.
    Uses Halley's method with cubic convergance rate.

    Pro:
    * converges even faster the Newton's method
    * useful when computing with *many* digits
    Contra:
    * needs first and second derivative of f
    * 3 function evaluations per iteration
    * converges slowly for multiple roots
    """

    maxsteps = 20

    def __init__(self, f, x0, **kwargs):
        if not len(x0) == 1:
            raise ValueError('expected 1 starting point, got %i' % len(x0))
        self.x0 = x0[0]
        self.f = f
        if not 'df' in kwargs:
            def df(x):
                return diff(f, x)
        else:
            df = kwargs['df']
        self.df = df
        if not 'd2f' in kwargs:
            def d2f(x):
                return diff(df, x)
        else:
            d2f = kwargs['df']
        self.d2f = d2f

    def __iter__(self):
        x = self.x0
        f = self.f
        df = self.df
        d2f = self.d2f
        while True:
            prevx = x
            fx = f(x)
            dfx = df(x)
            d2fx = d2f(x)
            x -=  2*fx*dfx / (2*dfx**2 - fx*d2fx)
            error = abs(x - prevx)
            yield x, error

class Muller:
    """
    1d-solver generating pairs of approximative root and error.

    Needs starting points x0, x1 and x2 close to the root.
    x1 defaults to x0 + 0.25; x2 to x1 + 0.25.
    Uses Muller's method that converges towards complex roots.

    Pro:
    * converges fast (somewhat faster than secant)
    * can find complex roots
    Contra:
    * converges slowly for multiple roots
    * may have complex values for real starting points and real roots

    http://en.wikipedia.org/wiki/M%C3%BCller%27s_method
    """
    maxsteps = 30

    def __init__(self, f, x0, **kwargs):
        if len(x0) == 1:
            self.x0 = x0[0]
            self.x1 = self.x0 + 0.25
            self.x2 = self.x1 + 0.25
        elif len(x0) == 2:
            self.x0 = x0[0]
            self.x1 = x0[1]
            self.x2 = self.x1 + 0.25
        elif len(x0) == 3:
            self.x0 = x0[0]
            self.x1 = x0[1]
            self.x2 = x0[2]
        else:
            raise ValueError('expected 1, 2 or 3 starting points, got %i'
                             % len(x0))
        self.f = f
        self.verbose = kwargs['verbose']

    def __iter__(self):
        f = self.f
        x0 = self.x0
        x1 = self.x1
        x2 = self.x2
        fx0 = f(x0)
        fx1 = f(x1)
        fx2 = f(x2)
        while True:
            # TODO: maybe refactoring with function for divided differences
            # calculate divided diffferences
            fx2x1 = (fx1 - fx2) / (x1 - x2)
            fx2x0 = (fx0 - fx2) / (x0 - x2)
            fx1x0 = (fx0 - fx1) / (x0 - x1)
            w = fx2x1 + fx2x0 - fx1x0
            fx2x1x0 = (fx1x0 - fx2x1) / (x0 - x2)
            if w == 0 and fx2x1x0 == 0:
                if self.verbose:
                    print 'canceled with'
                    print 'x0 =', x0, ', x1 =', x1, 'and x2 =', x2
                break
            x0 = x1
            fx0 = fx1
            x1 = x2
            fx1 = fx2
            # denominator should be as large as possible => choose sign
            r = sqrt(w**2 - 4*fx2*fx2x1x0)
            if abs(w - r) > abs(w + r):
                r = -r
            x2 -= 2*fx2 / (w + r)
            fx2 = f(x2)
            error = abs(x2 - x1)
            yield x2, error

# TODO: consider raising a ValueError when there's no sign change in a and b
class Bisection:
    """
    1d-solver generating pairs of approximative root and error.

    Uses bisection method to find a root of f in [a, b].
    Might fail for multiple roots (needs sign change).

    Pro:
    * robust and reliable
    Contra:
    * converges slowly
    * needs sign change
    """
    maxsteps = 100

    def __init__(self, f, x0, **kwargs):
        if len(x0) != 2:
            raise ValueError('expected interval of 2 points, got %i' * len(x0))
        self.f = f
        self.a = x0[0]
        self.b = x0[1]

    def __iter__(self):
        f = self.f
        a = self.a
        b = self.b
        l = b - a
        while True:
            m = 0.5 * (a + b) # TODO: ldexp?
            if f(m) * f(b) < 0:
                a = m
            else:
                b = m
            l /= 2
            yield (a + b)/2, abs(l)

def _getm(method):
    """
    Return a function to calculate m for Illinois-like methods.
    """
    if method == 'illinois':
        def getm(fz, fb):
            return 0.5
    elif method == 'pegasus':
        def getm(fz, fb):
            return fb/(fb + fz)
    elif method == 'anderson':
        def getm(fz, fb):
            m = 1 - fz/fb
            if m > 0:
                return m
            else:
                return 0.5
    else:
        raise ValueError, "method '%s' not recognized" % method
    return getm

class Illinois:
    """
    1d-solver generating pairs of approximative root and error.

    Uses Illinois method or similair to find a root of f in [a, b].
    Might fail for multiple roots (needs sign change).
    Combines bisect with secant (improved regula falsi).

    The only difference between the methods is the scaling factor m, which is
    used to ensure convergence (you can choose one using the 'method' keyword):
    Illinois method ('illinois'):       m = 0.5
    Pegasus method ('pegasus'):         m = fb/(fb + fz)
    Anderson-Björk method ('anderson'): m = 1 - fz/fb if positive else 0.5

    Pro:
    * converges very fast
    Contra:
    * has problems with multiple roots
    * needs sign change
    """
    maxsteps = 30

    def __init__(self, f, x0, **kwargs):
        if len(x0) != 2:
            raise ValueError('expected interval of 2 points, got %i' * len(x0))
        self.a = x0[0]
        self.b = x0[1]
        self.f = f
        self.tol = kwargs['tol']
        self.verbose = kwargs['verbose']
        self.method = kwargs.get('method', 'illinois')
        self.getm = _getm(self.method)
        if self.verbose:
            print 'using %s method' % self.method

    def __iter__(self):
        method = self.method
        f = self.f
        a = self.a
        b = self.b
        fa = f(a)
        fb = f(b)
        m = None
        while True:
            l = b - a
            if l == 0:
                break
            s = (fb - fa) / l
            z = a - fa/s
            fz = f(z)
            if abs(fz) < self.tol:
                # TODO: better condition (when f is very flat)
                if self.verbose:
                    print 'canceled with z =', z
                yield z, l
                break
            if fz * fb < 0: # root in [z, b]
                a = b
                fa = fb
                b = z
                fb = fz
            else: # root in [a, z]
                m = self.getm(fz, fb)
                b = z
                fb = fz
                fa = m*fa # scale down to ensure convergence
            if self.verbose and m and not method == 'illinois':
                print 'm:', m
            yield (a + b)/2, abs(l)

def Pegasus(*args, **kwargs):
    """
    1d-solver generating pairs of approximative root and error.

    Uses Pegasus method to find a root of f in [a, b].
    Wrapper for illinois to use method='pegasus'.
    """
    kwargs['method'] = 'pegasus'
    return Illinois(*args, **kwargs)

def Anderson(*args, **kwargs):
    u"""
    1d-solver generating pairs of approximative root and error.

    Uses Anderson-Björk method to find a root of f in [a, b].
    Wrapper for illinois to use method='pegasus'.
    """
    kwargs['method'] = 'anderson'
    return Illinois(*args, **kwargs)

# TODO: check whether it's possible to combine it with Illinois stuff
class Ridder:
    """
    1d-solver generating pairs of approximative root and error.

    Ridders' method to find a root of f in [a, b].
    Is told to perform as well as Brent's method while being simpler.

    Pro:
    * very fast
    * simpler than Brent's method
    Contra:
    * two function evaluations per step
    * has problems with multiple roots
    * needs sign change

    http://en.wikipedia.org/wiki/Ridders%27_method
    """
    maxsteps=30

    def __init__(self, f, x0, **kwargs):
        self.f = f
        if len(x0) != 2:
            raise ValueError('expected interval of 2 points, got %i' * len(x0))
        self.x1 = x0[0]
        self.x2 = x0[1]
        self.verbose = kwargs['verbose']
        self.tol = kwargs['tol']

    def __iter__(self):
        f = self.f
        x1 = self.x1
        fx1 = f(x1)
        x2 = self.x2
        fx2 = f(x2)
        while True:
            x3 = 0.5*(x1 + x2)
            fx3 = f(x3)
            x4 = x3 + (x3 - x1) * sign(fx1 - fx2) * fx3 / sqrt(fx3**2 - fx1*fx2)
            fx4 = f(x4)
            if abs(fx4) < self.tol:
                # TODO: better condition (when f is very flat)
                if self.verbose:
                    print 'canceled with f(x4) =', fx4
                yield x4, abs(x1 - x2)
                break
            if fx4 * fx2 < 0: # root in [x4, x2]
                x1 = x4
                fx1 = fx4
            else: # root in [x1, x4]
                x2 = x4
                fx2 = fx4
            error = abs(x1 - x2)
            yield (x1 + x2)/2, error

class ANewton:
    """
    EXPERIMENTAL 1d-solver generating pairs of approximative root and error.

    Uses Newton's method modified to use Steffensens method when convergence is
    slow. (I. e. for multiple roots.)
    """
    maxsteps = 20

    def __init__(self, f, x0, **kwargs):
        if not len(x0) == 1:
            raise ValueError('expected 1 starting point, got %i' * len(x0))
        self.x0 = x0[0]
        self.f = f
        if not 'df' in kwargs:
            def df(x):
                return diff(f, x)
        else:
            df = kwargs['df']
        self.df = df
        def phi(x):
            return x - f(x) / df(x)
        self.phi = phi
        self.verbose = kwargs['verbose']

    def __iter__(self):
        x0 = self.x0
        f = self.f
        df = self.df
        phi = self.phi
        error = 0
        counter = 0
        while True:
            prevx = x0
            try:
                x0 = phi(x0)
            except ZeroDivisionError:
                if self.verbose:
                    'ZeroDivisionError: canceled with x =', x0
                break
            preverror = error
            error = abs(prevx - x0)
            # TODO: decide not to use convergence acceleration
            if error and abs(error - preverror) / error < 1:
                if self.verbose:
                    print 'converging slowly'
                counter += 1
            if counter >= 3:
                # accelerate convergence
                phi = steffensen(phi)
                counter = 0
                if self.verbose:
                    print 'accelerating convergence'
            yield x0, error

# TODO: add Brent

#############
# UTILITIES #
#############

str2solver = {'secant':Secant,'mnewton':MNewton, 'halley':Halley,
              'muller':Muller, 'bisect':Bisection, 'illinois':Illinois,
              'pegasus':Pegasus, 'anderson':Anderson, 'ridder':Ridder,
              'anewton':ANewton}

@extraprec(20)
def findroot(f, x0, solver=Secant, tol=None, verbose=False, verify=True,
             force_type=convert_lossless, **kwargs):
    """
    Find a root of f using x0 as starting point or interval.

    If not abs(f(root)) < tol an exception is raised.

    Arguments:

    f : one dimensional function
    x0 : starting point, several starting points or interval (depends on solver)
    tol : the returned solution has an error smaller than this
    verbose : print additional information for each iteration if true
    verify : verify the solution and raise a ValueError if abs(f(x)) > tol
    force_type : use specified type constructor on starting points
    solver : a generator for f and x0 returning approximative solution and error
    maxsteps : after how many steps the solver will cancel
    df : first derivative of f (used by some solvers)
    d2f : second derivative of f (used by some solvers)

    solver has to be callable with (f, x0, **kwargs) and return an generator
    yielding pairs of approximative solution and estimated error.
    You can use the following string aliases:
    'secant', 'mnewton', 'halley', 'muller', 'illinois', 'pegasus', 'anderson',
    'ridder', 'anewton', 'bisect'
    See mpmath.optimization for their documentation.


    Examples
    ........

    The function ``findroot`` locates a root of a given function using the
    secant method by default. A simple example use of the secant method is to
    compute pi as the root of sin(*x*) closest to *x* = 3:

    >>> from mpmath import *
    >>> mp.dps = 30
    >>> print findroot(sin, 3)
    3.14159265358979323846264338328

    The secant method can be used to find complex roots of analytic functions,
    although it must in that case generally be given a nonreal starting value
    (or else it will never leave the real line):

    >>> mp.dps = 15
    >>> print findroot(lambda x: x**3 + 2*x + 1, j)
    (0.226698825758202 + 1.46771150871022j)

    A nice application is to compute nontrivial roots of the Riemann zeta
    function with many digits (good initial values are needed for convergence):

    >>> mp.dps = 30
    >>> print findroot(zeta, 0.5+14j)
    (0.5 + 14.1347251417346937904572519836j)

    The secant method can also be used as an optimization algorithm, by passing
    it a derivative of a function. The following example locates the positive
    minimum of the gamma function:

    >>> mp.dps = 20
    >>> print findroot(lambda x: diff(gamma, x), 1)
    1.4616321449683623413

    Finally, a useful application is to compute inverse functions, such as the
    Lambert W function which is the inverse of *w* exp(*w*), given the first
    term of the solution's asymptotic expansion as the initial value. In basic
    cases, this gives identical results to mpmath's builtin ``lambertw``
    function:

    >>> def lambert(x):
    ...     return findroot(lambda w: w*exp(w) - x, log(1+x))
    ...
    >>> mp.dps = 15
    >>> print lambert(1), lambertw(1)
    0.567143290409784 0.567143290409784
    >>> print lambert(1000), lambert(1000)
    5.2496028524016 5.2496028524016


    Multiple roots
    --------------

    For multiple roots all methods of the Newtonian family (including secant)
    converge slowly. Consider this example:

    >>> f = lambda x: (x - 1)**99
    >>> findroot(f, 0.9, verify=False)
    mpf('0.91807354244492868')

    Even for a very close starting point the secant method converges very
    slowly. Use ``verbose=True`` to illustrate this.

    It's possible to modify Newton's method to make it converge regardless of
    the root's multiplicity.

    >>> findroot(f, -10, solver='mnewton')
    mpf('1.0')

    This variant uses the first and second derivative of the function, which is
    not very efficient.

    Alternatively you can use an experimental Newtonian solver that keeps track
    of the speed of convergence and accelerates it using Steffensen's method if
    necessary.

    >>> findroot(f, -10, solver='anewton', verbose=True)
    x: -9.88888888888888888889
    error: 0.111111111111111111111
    converging slowly
    x: -9.77890011223344556678
    error: 0.10998877665544332211
    converging slowly
    x: -9.67002233332199662166
    error: 0.108877778911448945119
    converging slowly
    accelerating convergence
    x: -9.5622443299551077669
    error: 0.107778003366888854764
    converging slowly
    x: 0.99999999999999999214
    error: 10.562244329955107759
    x: 1.0
    error: 7.8598304758094664213e-18
    mpf('1.0')


    Complex roots
    -------------

    For complex roots it's recommended to use Muller's method as it converges
    even for real starting points very fast.

    >>> findroot(lambda x: x**4 + x + 1, (0, 1, 2), solver='muller')
    mpc(real='0.72713608449119684', imag='0.93409928946052944')


    Intersection methods
    --------------------

    When you need to find a root in a known interval, it's highly recommended to
    use an intersection-based solver like ``'anderson'`` or ``'ridder'``.
    Usually the converge faster and more reliable. They have however problems
    with multiple roots and usually need a sign change to find a root.

    >>> findroot(lambda x: x**3, (-1, 1), solver='anderson')
    mpf('0.0')

    Be careful with symmetric functions:

    >>> findroot(lambda x: x**2, (-1, 1), solver='anderson') #doctest:+ELLIPSIS
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "mpmath/settings.py", line 135, in g
        return f(*args, **kwargs)
      File "mpmath/optimization.py", line 551, in findroot
        for x, error in iterations:
      File "mpmath/optimization.py", line 332, in __iter__
        z = a - fa/s
      File "<string>", line 8, in __div__
      File ".../libmpf.py", line 761, in mpf_div
        raise ZeroDivisionError
    ZeroDivisionError

    It fails even for better starting points, because there is no sign change:

    >>> findroot(lambda x: x**2, (-1, .5), solver='anderson')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "mpmath/settings.py", line 135, in g
        return f(*args, **kwargs)
      File "mpmath/optimization.py", line 562, in findroot
        % (abs(f(x)), tol))
    ValueError: Could not find root within given tolerance. (1 > 2.1684e-19)
    Try another starting point or tweak arguments.
    """
    # initialize arguments
    if not force_type:
        force_type = lambda x: x
    elif not tol and (force_type == float or force_type == complex):
        tol = 2**(-52) # TODO: consider a less strict value
    kwargs['verbose'] = verbose
    if 'd1f' in kwargs:
        kwargs['df'] = kwargs['d1f']
    if tol is None:
        tol = eps * 2**10
    kwargs['tol'] = tol
    if isinstance(x0, (list, tuple)):
        x0 = [force_type(x) for x in x0]
    else:
        x0 = [force_type(x0)]
    if isinstance(solver, str):
        try:
            solver = str2solver[solver]
        except KeyError:
            raise ValueError('could not recognize solver')
    # use solver
    iterations = solver(f, x0, **kwargs)
    if 'maxsteps' in kwargs:
        maxsteps = kwargs['maxsteps']
    else:
        maxsteps = iterations.maxsteps
    i = 0
    for x, error in iterations:
        if verbose:
            print 'x:    ', x
            print 'error:', error
        i += 1
        if error < tol or i >= maxsteps:
            break
    if verify and abs(f(x))**2 > tol: # TODO: better condition?
        raise ValueError('Could not find root within given tolerance. '
                         '(%g > %g)\n'
                         'Try another starting point or tweak arguments.'
                         % (abs(f(x)), tol))
    return x

def multiplicity(f, root, tol=eps, maxsteps=10, **kwargs):
    """
    Return the multiplicity of a given root of f.

    Internally, numerical derivatives are used. This might be inefficient for
    higher order derviatives. Due to this, ``multiplicity`` cancels after
    evaluating 10 derivatives by default. You can be specify the n-th derivative
    using the dnf keyword.

    >>> from mpmath import *
    >>> multiplicity(lambda x: sin(x) - 1, pi/2)
    2
    """
    kwargs['d0f'] = f
    for i in xrange(maxsteps):
        dfstr = 'd' + str(i) + 'f'
        if dfstr in kwargs:
            df = kwargs[dfstr]
        else:
            df = lambda x: diff(f, x, i)
        if not abs(df(root)) < tol:
            break
    return i

def steffensen(f):
    """
    linear convergent function -> quadratic convergent function

    Steffensen's method for quadratic convergence of a linear converging
    sequence.
    Don not use it for higher rates of convergence.
    It may even work for divergent sequences.

    Definition:
    F(x) = (x*f(f(x)) - f(x)**2) / (f(f(x)) - 2*f(x) + x)

    Example
    .......

    You can use Steffensen's method to accelerate a fixpoint iteration of linear
    (or less) convergence.

    x* is a fixpoint of the iteration x_{k+1} = phi(x_k) if x* = phi(x*). For
    phi(x) = x**2 there are two fixpoints: 0 and 1. 

    Let's try Steffensen's method:

    >>> f = lambda x: x**2
    >>> from mpmath.optimization import steffensen
    >>> F = steffensen(f)
    >>> for x in [0.5, 0.9, 2.0]:
    ...     fx = Fx = x
    ...     for i in xrange(10):
    ...         try:
    ...             fx = f(fx)
    ...         except OverflowError:
    ...             pass
    ...         try:
    ...             Fx = F(Fx)
    ...         except ZeroDivisionError:
    ...             pass
    ...         print '%20g  %20g' % (fx, Fx)
                    0.25                  -0.5
                  0.0625                   0.1
              0.00390625            -0.0011236
            1.52588e-005          1.41691e-009
            2.32831e-010         -2.84465e-027
            5.42101e-020          2.30189e-080
            2.93874e-039          -1.2197e-239
            8.63617e-078                     0
            7.45834e-155                     0
            5.56268e-309                     0
                    0.81               1.02676
                  0.6561               1.00134
                0.430467                     1
                0.185302                     1
               0.0343368                     1
              0.00117902                     1
            1.39008e-006                     1
            1.93233e-012                     1
            3.73392e-024                     1
            1.39421e-047                     1
                       4                   1.6
                      16                1.2962
                     256               1.10194
                   65536               1.01659
            4.29497e+009               1.00053
            1.84467e+019                     1
            3.40282e+038                     1
            1.15792e+077                     1
            1.34078e+154                     1
            1.34078e+154                     1

    Unmodified, the iteration converges only towards 0. Modified it converges
    not only much faster, it converges even to the repelling fixpoint 1.
    """
    def F(x):
        fx = f(x)
        ffx = f(fx)
        return (x*ffx - fx**2) / (ffx - 2*fx + x)
    return F
