"""A framework for running unit test examples, written in docstrings.

This lets you write 'Ex: sqrt(4) ==> 2; sqrt(-1) raises ValueError' in the
docstring for sqrt, and then execute the examples as unit tests.

I realize now this is the same functionality as Tim Peters' doctest
module, but I started this in Python 2.0, and doctest first became an
official Python module in 2.1.  If you want heavy-duty functionality
and standardization, use doctest; if you want to make your docstrings
shorter, you might want docex.  (The name 'docex' connotes DOCstring
EXamples, a similarity to doctest, the literal 'Ex:', and a certain
package delivery service that also ends with 'ex', and offers fast
no-frills service.)

From Python, when you want to test modules m1, m2, ... do:
    docex.Test([m1, m2, ...])
From the shell, when you want to test files *.py, do:
    python docex.py *.py

For each module, Test looks at the __doc__ and _docex strings of the
module itself, and of each member, and recursively for each member
class.  If a line in a docstring starts with r'^\s*Ex: ' (a line with
blanks, then 'Ex: '), then the remainder of the string after the colon
is treated as examples. Each line of the examples should conform to
one of the following formats:

    (1) Blank line or a comment; these just get echoed verbatim to the log.
    (2) Of the form example1 ; example2 ; ...
    (3) Of the form 'x ==> y' for any expressions x and y.
            x is evaled and assigned to _, then y is evaled.
            If x != y, an error message is printed.
    (4) Of the form 'x raises y', for any statement x and expression y.
            First y is evaled to yield an exception type, then x is execed.
            If x doesn't raise the right exception, an error msg is printed.
    (5) Of the form 'statement'. Statement is execed for side effect.
    (6) Of the form 'expression'. Expression is evaled for side effect. 

My main reason for stubbornly sticking with my docex rather than doctest is
that I don't want a 10-line docstring for a 1-line function.
Compare doctest's 9-line test suite:
    >>> len('abc']
    3
    >>> len(range(5))
    5
    >>> len(5))
    Traceback (most recent call last):
      ...
    TypeError: len() of unsized object

with docex's 1-line version:
    Ex: len('abc') ==> 3; len(range(5)) ==> 5; len(5) raises TypeError

# You can also have statements and expressions without testing the result:
print 3 
2 + 1

# You can use _ if you need to do a more complex test on a result:
1./3.
0.333 < _ < 0.334 ==> 1

# Or do this if you don't need to see the value of 1./3. printed:
0.3333 < 1./3. < 0.334 ==> 1

# Now we have a quandry.  To show that Test() works, we need to try
# out failing tests.  But we want the final result to be zero failures.
# So we can't put '2 + 2 ==> 5' here, but we can do this:
t = Test([]); t.run_string('2 + 2 ='+'=> 5'); t
t.failed ==> 1
t = Test([]); t.run_string('0 rai'+'ses ZeroDivisionError'); t
t.failed ==> 1
"""

import re, sys, types

class Test:
    """A class to run test examples written in docstrings or in _docex."""

    def __init__(self, modules=None, title='Example output', out=None):
        if modules is None:
            modules = sys.modules.values()
        self.passed = self.failed = 0;
        self.dictionary = {}
        self.already_seen = {}
        try:
            if out: sys.stdout = out
            self.writeln('', """<head><title>%s</title></head>
            <body bgcolor=ffffff><h1>%s</h1><hr><pre>""" % (title, title))
            for module in modules:
                self.run_module(module)
            self.writeln(self, '<hr><h1>', '</h1></html>')
        finally:
            if out:
                sys.stdout = sys.__stdout__
                out.close()
                
    def __repr__(self):
	if self.failed:
            return ('<Test: #### failed %d, passed %d>'
                    % (self.failed, self.passed))
        else:
            return '<Test: passed all %d>' % self.passed

    def run_module(self, object):
        """Run the docstrings, and then all members of the module."""
        if not self.seen(object):
            self.dictionary.update(vars(object)) # import module into self
            self.writeln('## Module %s' % object.__name__,
                         '\n<table width="100%"><tr><td bgcolor=yellow><b>' +
                         '<a name="%s.py"><a href="%s.html">'
                         % (object.__name__, object.__name__),
                         '</a></a></b></table>')
            self.run_docstring(object)
            names = object.__dict__.keys()
            names.sort()
            for name in names:
                val = object.__dict__[name]
                if isinstance(val, types.ClassType):
                    self.run_class(val)
                elif isinstance(val, types.ModuleType):
                    pass
                elif not self.seen(val):
                    self.run_docstring(val)

    def run_class(self, object):
        """Run the docstrings, and then all members of the class."""
        if not self.seen(object):
            self.run_docstring(object)
            names = object.__dict__.keys()
            names.sort()
            for name in names:
                self.run_docstring(object.__dict__[name])

    def run_docstring(self, object, search=re.compile(r'(?m)^\s*Ex: ').search):
        "Run the __doc__ and _docex attributes, if the object has them."
        if hasattr(object, '__doc__'):
            s = object.__doc__
            if isinstance(s, str):
                match = search(s)
                if match: self.run_string(s[match.end():])
        if hasattr(object, '_docex'):
                self.run_string(object._docex)
        
    def run_string(self, teststr):
        """Run a test string, printing inputs and results."""
        if not teststr: return
        teststr = teststr.strip()
        if not teststr: return
        if teststr.find('\n') > -1:
            map(self.run_string, teststr.split('\n'))
        elif teststr.startswith('#'):
            self.writeln(teststr)
        elif teststr.find('; ') > -1:
            for substr in teststr.split('; '): self.run_string(substr)
        elif teststr.find('==>') > -1:
            teststr, result = teststr.split('==>')
            self.evaluate(teststr, result)
        elif teststr.find(' raises ') > -1:
            teststr, exception = teststr.split(' raises ')
            self.raises(teststr, exception)
        else: ## Try to eval, but if it is a statement, exec
            try:
                self.evaluate(teststr)
            except SyntaxError:
                exec teststr in self.dictionary

    def evaluate(self, teststr, resultstr=None):
        "Eval teststr and check if resultstr (if given) evals to the same."
        self.writeln('>>> ' +  teststr.strip())
        result = eval(teststr, self.dictionary)
        self.dictionary['_'] = result
        self.writeln(repr(result))
        if resultstr == None:
          return
        elif result == eval(resultstr, self.dictionary):
          self.passed += 1
        else:
          self.fail(teststr, resultstr)
    
    def raises(self, teststr, exceptionstr):
        teststr = teststr.strip()
        self.writeln('>>> ' + teststr)
        except_class = eval(exceptionstr, self.dictionary)
        try:
            exec teststr in self.dictionary
        except except_class:
            self.writeln('# raises %s as expected' % exceptionstr)
            self.passed += 1
            return
        self.fail(teststr, exceptionstr)

    def fail(self, teststr, resultstr):
        self.writeln('###### ERROR: expected %s for %s' % (resultstr, teststr),
                     '<font color=red><b>', '</b></font>')
        self.failed += 1

    def writeln(self, s, before='', after=''):
        "Write s, wrapped with before and after."
        s = str(s)
        s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        print '%s%s%s' % (before, s, after)

    def seen(self, object):
        """Return true if this object has been seen before.
        In any case, record that we have seen it."""
        result = self.already_seen.has_key(id(object))
        self.already_seen[id(object)] = 1
        return result

def main(args):
    modules = [__import__(a[:-3]) for a in args if a.endswith('.py')]
    print Test(modules, out=open('docex-log.html', 'w'))

if __name__ == '__main__':
    main(sys.argv[1:])
