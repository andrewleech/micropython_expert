|**Library**|**Description**|**MicroPython Status**|**Notes**|
|---|---|---|---|
| [__future__](https://docs.python.org/3/library/__future__.html#module-__future__) |  Future statement definitions | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/__future__)
| [__main__](https://docs.python.org/3/library/__main__.html#module-__main__) |  The environment where the top-level script is run. | ✅ | 
| [_thread](https://docs.python.org/3/library/_thread.html#module-_thread) |  Low-level threading API. | ✅ | See [[Threads]] for more info. |
| [abc](https://docs.python.org/3/library/abc.html#module-abc) |  Abstract base classes according to :pep:`3119`. | ❌ | Placeholder in [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/abc)
| [argparse](https://docs.python.org/3/library/argparse.html#module-argparse) |  Command-line option and argument parsing library. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/argparse)
| [array](https://docs.python.org/3/library/array.html#module-array) |  Space efficient arrays of uniformly typed numeric values. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/uarray.html)
| [ast](https://docs.python.org/3/library/ast.html#module-ast) |  Abstract Syntax Tree classes and manipulation. | ❌ | Requires `_ast` to be implemented in core MicroPython.
| [asyncio](https://docs.python.org/3/library/asyncio.html#module-asyncio) |  Asynchronous I/O. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/uasyncio.html)
| [atexit](https://docs.python.org/3/library/atexit.html#module-atexit) |  Register and execute cleanup functions. | ❌ | `atexit` module itself is not implemented in MicroPython, but the `atexit.register()` functionality is largely implemented via `sys.atexit()`
| [base64](https://docs.python.org/3/library/base64.html#module-base64) |  RFC 3548: Base16, Base32, Base64 Data Encodings; Base85 and Ascii85 | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/base64)
| [bdb](https://docs.python.org/3/library/bdb.html#module-bdb) |  Debugger framework. | ❌ | 
| [binascii](https://docs.python.org/3/library/binascii.html#module-binascii) |  Tools for converting between binary and various ASCII-encoded binary representations. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/binascii.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/binascii)
| [binhex](https://docs.python.org/3/library/binhex.html#module-binhex) |  Encode and decode files in binhex4 format. | ❌ | Deprecated since CPython 3.9
| [bisect](https://docs.python.org/3/library/bisect.html#module-bisect) |  Array bisection algorithms for binary searching. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/bisect)
| [builtins](https://docs.python.org/3/library/builtins.html#module-builtins) |  The module that provides the built-in namespace. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/builtins.html) 
| [bz2](https://docs.python.org/3/library/bz2.html#module-bz2) |  Interfaces for bzip2 compression and decompression. | ❌ | 
| [calendar](https://docs.python.org/3/library/calendar.html#module-calendar) |  Functions for working with calendars, including some emulation of the Unix cal program. | ❌ | See [#521](https://github.com/micropython/micropython-lib/pull/521)
| [cmath](https://docs.python.org/3/library/cmath.html#module-cmath) |  Mathematical functions for complex numbers. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/cmath.html)
| [cmd](https://docs.python.org/3/library/cmd.html#module-cmd) |  Build line-oriented command interpreters. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/cmd)
| [code](https://docs.python.org/3/library/code.html#module-code) |  Facilities to implement read-eval-print loops. | ❌ | 
| [codecs](https://docs.python.org/3/library/codecs.html#module-codecs) |  Encode and decode data and streams. | ❌ | 
| [codeop](https://docs.python.org/3/library/codeop.html#module-codeop) |  Compile (possibly incomplete) Python code. | ❌ | 
| [collections](https://docs.python.org/3/library/collections.html#module-collections) |  Container datatypes | 🟡 | See [[Collections module]] for more info. |
| [collections.abc](https://docs.python.org/3/library/collections.abc.html#module-collections.abc) |  Abstract base classes for containers | ❌ | 
| [colorsys](https://docs.python.org/3/library/colorsys.html#module-colorsys) |  Conversion functions between RGB and other color systems. | 🟡 | Implementation proposed in [Micropython Lib #452](https://github.com/micropython/micropython-lib/pull/452)
| [compileall](https://docs.python.org/3/library/compileall.html#module-compileall) |  Tools for byte-compiling all Python source files in a directory tree. | ❌ | 
| concurrent |   | ? | 
| [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures) |  Execute computations concurrently using threads or processes. | ? | 
| [configparser](https://docs.python.org/3/library/configparser.html#module-configparser) |  Configuration file parser. | ? | 
| [contextlib](https://docs.python.org/3/library/contextlib.html#module-contextlib) |  Utilities for with-statement contexts. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/contextlib)
| [contextvars](https://docs.python.org/3/library/contextvars.html#module-contextvars) |  Context Variables | ? | 
| [copy](https://docs.python.org/3/library/copy.html#module-copy) |  Shallow and deep copy operations. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/copy)
| [copyreg](https://docs.python.org/3/library/copyreg.html#module-copyreg) |  Register pickle support functions. | ? | 
| [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile) |   | ? | 
| [csv](https://docs.python.org/3/library/csv.html#module-csv) |  Write and read tabular data to and from delimited files. | ❌ | CPython splits the implementation into a Python module, [csv.py](https://github.com/python/cpython/blob/main/Lib/csv.py), and a C module, [_csv.c](https://github.com/python/cpython/blob/main/Modules/_csv.c). It might be possible to port _csv.c and use csv.py directly.
| [ctypes](https://docs.python.org/3/library/ctypes.html#module-ctypes) |  A foreign function library for Python. | 🟡 | See [uctypes](https://docs.micropython.org/en/latest/library/uctypes.html). Different to CPython to reduce memory use.
| [curses](https://docs.python.org/3/library/curses.html#module-curses) |  An interface to the curses library, providing portable terminal handling. | ? | 
| [curses.ascii](https://docs.python.org/3/library/curses.ascii.html#module-curses.ascii) |  Constants and set-membership functions for ASCII characters. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/curses.ascii)
| [curses.panel](https://docs.python.org/3/library/curses.panel.html#module-curses.panel) |  A panel stack extension that adds depth to  curses windows. | ? | 
| [curses.textpad](https://docs.python.org/3/library/curses.html#module-curses.textpad) |  Emacs-like input editing in a curses window. | ? | 
| [dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses) |  Generate special methods on user-defined classes. | ? | 
| [datetime](https://docs.python.org/3/library/datetime.html#module-datetime) |  Basic date and time types. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/datetime)
| [dbm](https://docs.python.org/3/library/dbm.html#module-dbm) |  Interfaces to various Unix "database" formats. | ? | 
| [dbm.dumb](https://docs.python.org/3/library/dbm.html#module-dbm.dumb) |  Portable implementation of the simple DBM interface. | ? | 
| [dbm.gnu](https://docs.python.org/3/library/dbm.html#module-dbm.gnu) |  GNU's reinterpretation of dbm. | ? | 
| [dbm.ndbm](https://docs.python.org/3/library/dbm.html#module-dbm.ndbm) |  The standard "database" interface, based on ndbm. | ? | 
| [decimal](https://docs.python.org/3/library/decimal.html#module-decimal) |  Implementation of the General Decimal Arithmetic  Specification. | 🟡 | See third-part [mpy-decimal](https://github.com/mpy-dev/micropython-decimal-number).
| [difflib](https://docs.python.org/3/library/difflib.html#module-difflib) |  Helpers for computing differences between objects. | ? | 
| [dis](https://docs.python.org/3/library/dis.html#module-dis) |  Disassembler for Python bytecode. | ? | 
| [distutils](https://docs.python.org/3/library/distutils.html#module-distutils) and submodules |  Support for building and installing Python modules into an existing Python installation. | ❌ | 
| [doctest](https://docs.python.org/3/library/doctest.html#module-doctest) |  Test pieces of code within docstrings. | ? | 
| [email](https://docs.python.org/3/library/email.html#module-email) |  Package supporting the parsing, manipulating, and generating email messages. | ? | 
| [email.charset](https://docs.python.org/3/library/email.charset.html#module-email.charset) |  Character Sets | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.charset)
| [email.contentmanager](https://docs.python.org/3/library/email.contentmanager.html#module-email.contentmanager) |  Storing and Retrieving Content from MIME Parts | ? | 
| [email.encoders](https://docs.python.org/3/library/email.encoders.html#module-email.encoders) |  Encoders for email message payloads. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.encoders)
| [email.errors](https://docs.python.org/3/library/email.errors.html#module-email.errors) |  The exception classes used by the email package. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.errors)
| [email.generator](https://docs.python.org/3/library/email.generator.html#module-email.generator) |  Generate flat text email messages from a message structure. | ? | 
| [email.header](https://docs.python.org/3/library/email.header.html#module-email.header) |  Representing non-ASCII headers | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.header)
| [email.headerregistry](https://docs.python.org/3/library/email.headerregistry.html#module-email.headerregistry) |  Automatic Parsing of headers based on the field name | ? | 
| [email.iterators](https://docs.python.org/3/library/email.iterators.html#module-email.iterators) |  Iterate over a  message object tree. | ? | 
| [email.message](https://docs.python.org/3/library/email.message.html#module-email.message) |  The base class representing email messages. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.message)
| [email.mime](https://docs.python.org/3/library/email.mime.html#module-email.mime) |  Build MIME messages. | ? | 
| [email.parser](https://docs.python.org/3/library/email.parser.html#module-email.parser) |  Parse flat text email messages to produce a message object structure. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.parser)
| [email.policy](https://docs.python.org/3/library/email.policy.html#module-email.policy) |  Controlling the parsing and generating of messages | ? | 
| [email.utils](https://docs.python.org/3/library/email.utils.html#module-email.utils) |  Miscellaneous email package utilities. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/email.utils)
| encodings |   | ? | 
| [encodings.idna](https://docs.python.org/3/library/codecs.html#module-encodings.idna) |  Internationalized Domain Names implementation | ? | 
| [encodings.mbcs](https://docs.python.org/3/library/codecs.html#module-encodings.mbcs) |  Windows ANSI codepage | ? | 
| [encodings.utf_8_sig](https://docs.python.org/3/library/codecs.html#module-encodings.utf_8_sig) |  UTF-8 codec with BOM signature | ? | 
| [ensurepip](https://docs.python.org/3/library/ensurepip.html#module-ensurepip) |  Bootstrapping the "pip" installer into an existing Python installation or virtual environment. | ? | 
| [enum](https://docs.python.org/3/library/enum.html#module-enum) |  Implementation of an enumeration class. | ❌ | Metaclasses are not yet supported in MicroPython and it's challenging to provide enum support without it. 
| [errno](https://docs.python.org/3/library/errno.html#module-errno) |  Standard errno system symbols. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/errno.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/errno)
| [faulthandler](https://docs.python.org/3/library/faulthandler.html#module-faulthandler) |  Dump the Python traceback. | ? | 
| [fcntl](https://docs.python.org/3/library/fcntl.html#module-fcntl) |  The fcntl() and ioctl() system calls. | ? | 
| [filecmp](https://docs.python.org/3/library/filecmp.html#module-filecmp) |  Compare files efficiently. | ? | 
| [fileinput](https://docs.python.org/3/library/fileinput.html#module-fileinput) |  Loop over standard input or a list of files. | ? | 
| [fnmatch](https://docs.python.org/3/library/fnmatch.html#module-fnmatch) |  Unix shell style filename pattern matching. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/fnmatch)
| [formatter](https://docs.python.org/3/library/formatter.html#module-formatter) | Deprecated: Generic output formatter and device interface. | ? | 
| [fractions](https://docs.python.org/3/library/fractions.html#module-fractions) |  Rational numbers. | ? | See WIP [micropython-fractions](https://github.com/mattytrentini/micropython-fractions)
| [ftplib](https://docs.python.org/3/library/ftplib.html#module-ftplib) |  FTP protocol client (requires sockets). | ? | 
| [functools](https://docs.python.org/3/library/functools.html#module-functools) |  Higher-order functions and operations on callable objects. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/functools)
| [gc](https://docs.python.org/3/library/gc.html#module-gc) |  Interface to the cycle-detecting garbage collector. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/gc.html)
| [getopt](https://docs.python.org/3/library/getopt.html#module-getopt) |  Portable parser for command line options; support both short and long option names. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/getopt)
| [getpass](https://docs.python.org/3/library/getpass.html#module-getpass) |  Portable reading of passwords and retrieval of the userid. | ? | 
| [gettext](https://docs.python.org/3/library/gettext.html#module-gettext) |  Multilingual internationalization services. | ? | 
| [glob](https://docs.python.org/3/library/glob.html#module-glob) |  Unix shell style pathname pattern expansion. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/glob)
| [graphlib](https://docs.python.org/3/library/graphlib.html#module-graphlib) |  Functionality to operate with graph-like structures | ? | 
| [grp](https://docs.python.org/3/library/grp.html#module-grp) |  The group database (getgrnam() and friends). | ? | 
| [gzip](https://docs.python.org/3/library/gzip.html#module-gzip) |  Interfaces for gzip compression and decompression using file objects. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/gzip)
| [hashlib](https://docs.python.org/3/library/hashlib.html#module-hashlib) |  Secure hash and message digest algorithms. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/hashlib.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/hashlib)
| [heapq](https://docs.python.org/3/library/heapq.html#module-heapq) |  Heap queue algorithm (a.k.a. priority queue). | ✅ | [built-in](https://docs.micropython.org/en/latest/library/heapq.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/heapq)
| [hmac](https://docs.python.org/3/library/hmac.html#module-hmac) |  Keyed-Hashing for Message Authentication (HMAC) implementation | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/hmac)
| [html](https://docs.python.org/3/library/html.html#module-html) |  Helpers for manipulating HTML. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/html)
| [html.entities](https://docs.python.org/3/library/html.entities.html#module-html.entities) |  Definitions of HTML general entities. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/html.entities)
| [html.parser](https://docs.python.org/3/library/html.parser.html#module-html.parser) |  A simple parser that can handle HTML and XHTML. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/html.parser)
| [http](https://docs.python.org/3/library/http.html#module-http) |  HTTP status codes and messages | ? | 
| [http.client](https://docs.python.org/3/library/http.client.html#module-http.client) |  HTTP and HTTPS protocol client (requires sockets). | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/http.client)
| [http.cookiejar](https://docs.python.org/3/library/http.cookiejar.html#module-http.cookiejar) |  Classes for automatic handling of HTTP cookies. | ? | 
| [http.cookies](https://docs.python.org/3/library/http.cookies.html#module-http.cookies) |  Support for HTTP state management (cookies). | ? | 
| [http.server](https://docs.python.org/3/library/http.server.html#module-http.server) |  HTTP server and request handlers. | ? | 
| [imaplib](https://docs.python.org/3/library/imaplib.html#module-imaplib) |  IMAP4 protocol client (requires sockets). | ? | 
| [imp](https://docs.python.org/3/library/imp.html#module-imp) | Deprecated: Access the implementation of the import statement. | ? | 
| [importlib](https://docs.python.org/3/library/importlib.html#module-importlib) |  The implementation of the import machinery. | ? | 
| [importlib.abc](https://docs.python.org/3/library/importlib.html#module-importlib.abc) |  Abstract base classes related to import | ? | 
| [importlib.machinery](https://docs.python.org/3/library/importlib.html#module-importlib.machinery) |  Importers and path hooks | ? | 
| [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#module-importlib.metadata) |  The implementation of the importlib metadata. | ? | 
| [importlib.resources](https://docs.python.org/3/library/importlib.html#module-importlib.resources) |  Package resource reading, opening, and access | ? | 
| [importlib.util](https://docs.python.org/3/library/importlib.html#module-importlib.util) |  Utility code for importers | ? | 
| [inspect](https://docs.python.org/3/library/inspect.html#module-inspect) |  Extract information and source code from live objects. | 🟡 | Some of inspect is available at [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/inspect)
| [io](https://docs.python.org/3/library/io.html#module-io) |  Core tools for working with streams. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/io.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/io)
| [ipaddress](https://docs.python.org/3/library/ipaddress.html#module-ipaddress) |  IPv4/IPv6 manipulation library. | ? | 
| [itertools](https://docs.python.org/3/library/itertools.html#module-itertools) |  Functions creating iterators for efficient looping. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/itertools)
| [json](https://docs.python.org/3/library/json.html#module-json) |  Encode and decode the JSON format. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/json.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/json)
| [json.tool](https://docs.python.org/3/library/json.html#module-json.tool) |  A command line to validate and pretty-print JSON. | ? | 
| [keyword](https://docs.python.org/3/library/keyword.html#module-keyword) |  Test whether a string is a keyword in Python. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/keyword)
| [lib2to3](https://docs.python.org/3/library/2to3.html#module-lib2to3) |  The 2to3 library | ? | 
| [linecache](https://docs.python.org/3/library/linecache.html#module-linecache) |  Provides random access to individual lines from text files. | ❌ | 
| [locale](https://docs.python.org/3/library/locale.html#module-locale) |  Internationalization services. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/locale)
| [logging](https://docs.python.org/3/library/logging.html#module-logging) |  Flexible event logging system for applications. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/logging)
| [logging.config](https://docs.python.org/3/library/logging.config.html#module-logging.config) |  Configuration of the logging module. | ? | 
| [logging.handlers](https://docs.python.org/3/library/logging.handlers.html#module-logging.handlers) |  Handlers for the logging module. | ? | 
| [lzma](https://docs.python.org/3/library/lzma.html#module-lzma) |  A Python wrapper for the liblzma compression library. | ? | 
| [mailbox](https://docs.python.org/3/library/mailbox.html#module-mailbox) |  Manipulate mailboxes in various formats | ? | 
| [mailcap](https://docs.python.org/3/library/mailcap.html#module-mailcap) |  Mailcap file handling. | ? | 
| [marshal](https://docs.python.org/3/library/marshal.html#module-marshal) |  Convert Python objects to streams of bytes and back (with different constraints). | ? | 
| [math](https://docs.python.org/3/library/math.html#module-math) |  Mathematical functions (sin() etc.). | ✅ | [built-in](https://docs.micropython.org/en/latest/library/math.html)
| [mimetypes](https://docs.python.org/3/library/mimetypes.html#module-mimetypes) |  Mapping of filename extensions to MIME types. | ? | 
| [mmap](https://docs.python.org/3/library/mmap.html#module-mmap) |  Interface to memory-mapped files for Unix and Windows. | ? | 
| [modulefinder](https://docs.python.org/3/library/modulefinder.html#module-modulefinder) |  Find modules used by a script. | ? | 
| [msvcrt](https://docs.python.org/3/library/msvcrt.html#module-msvcrt) |  Miscellaneous useful routines from the MS VC++ runtime. | ? | 
| [multiprocessing](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing) |  Process-based parallelism. | ? | 
| [multiprocessing.connection](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.connection) |  API for dealing with sockets. | ? | 
| [multiprocessing.dummy](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.dummy) |  Dumb wrapper around threading. | ? | 
| [multiprocessing.managers](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.managers) |  Share data between process with shared objects. | ? | 
| [multiprocessing.pool](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool) |  Create pools of processes. | ? | 
| [multiprocessing.shared_memory](https://docs.python.org/3/library/multiprocessing.shared_memory.html#module-multiprocessing.shared_memory) |  Provides shared memory for direct access across processes. | ? | 
| [multiprocessing.sharedctypes](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.sharedctypes) |  Allocate ctypes objects from shared memory. | ? | 
| [netrc](https://docs.python.org/3/library/netrc.html#module-netrc) |  Loading of .netrc files. | ? | 
| [numbers](https://docs.python.org/3/library/numbers.html#module-numbers) |  Numeric abstract base classes (Complex, Real, Integral, etc.). | ? | 
| [operator](https://docs.python.org/3/library/operator.html#module-operator) |  Functions corresponding to the standard operators. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/operator)
| [optparse](https://docs.python.org/3/library/optparse.html#module-optparse) | Deprecated: Command-line option parsing library. | ? | 
| [os](https://docs.python.org/3/library/os.html#module-os) |  Miscellaneous operating system interfaces. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/os.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/os)
| [os.path](https://docs.python.org/3/library/os.path.html#module-os.path) |  Operations on pathnames. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/os.path)
| [parser](https://docs.python.org/3/library/parser.html#module-parser) |  Access parse trees for Python source code. | ? | 
| [pathlib](https://docs.python.org/3/library/pathlib.html#module-pathlib) |  Object-oriented filesystem paths | ? | 
| [pdb](https://docs.python.org/3/library/pdb.html#module-pdb) |  The Python debugger for interactive interpreters. | ? | See WIP micropython-lib PR #[499](https://github.com/micropython/micropython-lib/pull/499)
| [pickle](https://docs.python.org/3/library/pickle.html#module-pickle) |  Convert Python objects to streams of bytes and back. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/pickle)
| [pickletools](https://docs.python.org/3/library/pickletools.html#module-pickletools) |  Contains extensive comments about the pickle protocols and pickle-machine opcodes, as well as some useful functions. | ? | 
| [pkgutil](https://docs.python.org/3/library/pkgutil.html#module-pkgutil) |  Utilities for the import system. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/pkgutil)
| [platform](https://docs.python.org/3/library/platform.html#module-platform) |  Retrieves as much platform identifying data as possible. | ? | 
| [plistlib](https://docs.python.org/3/library/plistlib.html#module-plistlib) |  Generate and parse Apple plist files. | ? | 
| [poplib](https://docs.python.org/3/library/poplib.html#module-poplib) |  POP3 protocol client (requires sockets). | ? | 
| [posix](https://docs.python.org/3/library/posix.html#module-posix) |  The most common POSIX system calls (normally used via module os). | ? | 
| [pprint](https://docs.python.org/3/library/pprint.html#module-pprint) |  Data pretty printer. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/pprint)
| [profile](https://docs.python.org/3/library/profile.html#module-profile) |  Python source profiler. | ? | 
| [pstats](https://docs.python.org/3/library/profile.html#module-pstats) |  Statistics object for use with the profiler. | ? | 
| [pty](https://docs.python.org/3/library/pty.html#module-pty) |  Pseudo-Terminal Handling for Linux. | ? | 
| [pwd](https://docs.python.org/3/library/pwd.html#module-pwd) |  The password database (getpwnam() and friends). | ? | 
| [py_compile](https://docs.python.org/3/library/py_compile.html#module-py_compile) |  Generate byte-code files from Python source files. | ? | 
| [pyclbr](https://docs.python.org/3/library/pyclbr.html#module-pyclbr) |  Supports information extraction for a Python module browser. | ? | 
| [pydoc](https://docs.python.org/3/library/pydoc.html#module-pydoc) |  Documentation generator and online help system. | ? | 
| [queue](https://docs.python.org/3/library/queue.html#module-queue) |  A synchronized queue class. | ? | 
| [quopri](https://docs.python.org/3/library/quopri.html#module-quopri) |  Encode and decode files using the MIME quoted-printable encoding. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/quopri)
| [random](https://docs.python.org/3/library/random.html#module-random) |  Generate pseudo-random numbers with various common distributions. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/random.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/random)
| [re](https://docs.python.org/3/library/re.html#module-re) |  Regular expression operations. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/ure.html)
| [readline](https://docs.python.org/3/library/readline.html#module-readline) |  GNU readline support for Python. | ? | 
| [reprlib](https://docs.python.org/3/library/reprlib.html#module-reprlib) |  Alternate repr() implementation with size limits. | ? | 
| [resource](https://docs.python.org/3/library/resource.html#module-resource) |  An interface to provide resource usage information on the current process. | ? | 
| [rlcompleter](https://docs.python.org/3/library/rlcompleter.html#module-rlcompleter) |  Python identifier completion, suitable for the GNU readline library. | ? | 
| [runpy](https://docs.python.org/3/library/runpy.html#module-runpy) |  Locate and run Python modules without importing them first. | ? | 
| [sched](https://docs.python.org/3/library/sched.html#module-sched) |  General purpose event scheduler. | ? | 
| [secrets](https://docs.python.org/3/library/secrets.html#module-secrets) |  Generate secure random numbers for managing secrets. | ? | 
| [select](https://docs.python.org/3/library/select.html#module-select) |  Wait for I/O completion on multiple streams. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/uselect.html)
| [selectors](https://docs.python.org/3/library/selectors.html#module-selectors) |  High-level I/O multiplexing. | ? | 
| [shelve](https://docs.python.org/3/library/shelve.html#module-shelve) |  Python object persistence. | ? | 
| [shlex](https://docs.python.org/3/library/shlex.html#module-shlex) |  Simple lexical analysis for Unix shell-like languages. | ? | 
| [shutil](https://docs.python.org/3/library/shutil.html#module-shutil) |  High-level file operations, including copying. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/shutil)
| [signal](https://docs.python.org/3/library/signal.html#module-signal) |  Set handlers for asynchronous events. | ? | 
| [site](https://docs.python.org/3/library/site.html#module-site) |  Module responsible for site-specific configuration. | ? | 
| [smtplib](https://docs.python.org/3/library/smtplib.html#module-smtplib) |  SMTP protocol client (requires sockets). | ? | 
| [socket](https://docs.python.org/3/library/socket.html#module-socket) |  Low-level networking interface. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/socket.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/socket)
| [socketserver](https://docs.python.org/3/library/socketserver.html#module-socketserver) |  A framework for network servers. | ? | 
| [sqlite3](https://docs.python.org/3/library/sqlite3.html#module-sqlite3) |  A DB-API 2.0 implementation using SQLite 3.x. | ? | 
| [ssl](https://docs.python.org/3/library/ssl.html#module-ssl) |  TLS/SSL wrapper for socket objects | ✅ | [built-in](https://docs.micropython.org/en/latest/library/ssl.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/ssl)
| [stat](https://docs.python.org/3/library/stat.html#module-stat) |  Utilities for interpreting the results of os.stat(), os.lstat() and os.fstat(). | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/stat)
| [statistics](https://docs.python.org/3/library/statistics.html#module-statistics) |  Mathematical statistics functions | ? | 
| [string](https://docs.python.org/3/library/string.html#module-string) |  Common string operations. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/string)
| [stringprep](https://docs.python.org/3/library/stringprep.html#module-stringprep) |  String preparation, as per RFC 3453 | ? | 
| [struct](https://docs.python.org/3/library/struct.html#module-struct) |  Interpret bytes as packed binary data. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/struct.html) and [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/struct)
| [subprocess](https://docs.python.org/3/library/subprocess.html#module-subprocess) |  Subprocess management. | ? | 
| [symbol](https://docs.python.org/3/library/symbol.html#module-symbol) |  Constants representing internal nodes of the parse tree. | ? | 
| [symtable](https://docs.python.org/3/library/symtable.html#module-symtable) |  Interface to the compiler's internal symbol tables. | ? | 
| [sys](https://docs.python.org/3/library/sys.html#module-sys) |  Access system-specific parameters and functions. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/usys.html)
| [sysconfig](https://docs.python.org/3/library/sysconfig.html#module-sysconfig) |  Python's configuration information | ? | 
| [syslog](https://docs.python.org/3/library/syslog.html#module-syslog) |  An interface to the Unix syslog library routines. | ? | 
| [tabnanny](https://docs.python.org/3/library/tabnanny.html#module-tabnanny) |  Tool for detecting white space related problems in Python source files in a directory tree. | ? | 
| [tarfile](https://docs.python.org/3/library/tarfile.html#module-tarfile) |  Read and write tar-format archive files. | ? | 
| [tempfile](https://docs.python.org/3/library/tempfile.html#module-tempfile) |  Generate temporary files and directories. | ? | 
| [termios](https://docs.python.org/3/library/termios.html#module-termios) |  POSIX style tty control. | ? | 
| [test](https://docs.python.org/3/library/test.html#module-test) |  Regression tests package containing the testing suite for Python. | ? | 
| [test.support](https://docs.python.org/3/library/test.html#module-test.support) |  Support for Python's regression test suite. | ? | 
| [test.support.bytecode_helper](https://docs.python.org/3/library/test.html#module-test.support.bytecode_helper) |  Support tools for testing correct bytecode generation. | ? | 
| [test.support.script_helper](https://docs.python.org/3/library/test.html#module-test.support.script_helper) |  Support for Python's script execution tests. | ? | 
| [test.support.socket_helper](https://docs.python.org/3/library/test.html#module-test.support.socket_helper) |  Support for socket tests. | ? | 
| [textwrap](https://docs.python.org/3/library/textwrap.html#module-textwrap) |  Text wrapping and filling | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/textwrap)
| [threading](https://docs.python.org/3/library/threading.html#module-threading) |  Thread-based parallelism. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/threading)
| [time](https://docs.python.org/3/library/time.html#module-time) |  Time access and conversions. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/utime.html)
| [timeit](https://docs.python.org/3/library/timeit.html#module-timeit) |  Measure the execution time of small code snippets. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/timeit)
| [tkinter](https://docs.python.org/3/library/tkinter.html#module-tkinter) and submodules |  Interface to Tcl/Tk for graphical user interfaces | ❌ | 
| [token](https://docs.python.org/3/library/token.html#module-token) |  Constants representing terminal nodes of the parse tree. | ? | 
| [tokenize](https://docs.python.org/3/library/tokenize.html#module-tokenize) |  Lexical scanner for Python source code. | ❌ | 
| [trace](https://docs.python.org/3/library/trace.html#module-trace) |  Trace or track Python statement execution. | ? | 
| [traceback](https://docs.python.org/3/library/traceback.html#module-traceback) |  Print or retrieve a stack traceback. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/traceback)
| [tracemalloc](https://docs.python.org/3/library/tracemalloc.html#module-tracemalloc) |  Trace memory allocations. | ? | 
| [tty](https://docs.python.org/3/library/tty.html#module-tty) |  Utility functions that perform common terminal control operations. | ? | 
| [turtle](https://docs.python.org/3/library/turtle.html#module-turtle) |  An educational framework for simple graphics applications | ? | 
| [turtledemo](https://docs.python.org/3/library/turtle.html#module-turtledemo) |  A viewer for example turtle scripts | ? | 
| [types](https://docs.python.org/3/library/types.html#module-types) |  Names for built-in types. | 🟡 | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/types) (missing at least `MappingProxyType`, maybe more)
| [typing](https://docs.python.org/3/library/typing.html#module-typing) |  Support for type hints (see :pep:`484`). | ? | 
| [unicodedata](https://docs.python.org/3/library/unicodedata.html#module-unicodedata) |  Access the Unicode Database. | ? | 
| [unittest](https://docs.python.org/3/library/unittest.html#module-unittest) |  Unit testing framework for Python. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/unittest)
| [unittest.mock](https://docs.python.org/3/library/unittest.mock.html#module-unittest.mock) |  Mock object library. | ? | 
| [urllib](https://docs.python.org/3/library/urllib.html#module-urllib) |   | ? | 
| [urllib.error](https://docs.python.org/3/library/urllib.error.html#module-urllib.error) |  Exception classes raised by urllib.request. | ? | 
| [urllib.parse](https://docs.python.org/3/library/urllib.parse.html#module-urllib.parse) |  Parse URLs into or assemble them from components. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/urllib.parse)
| [urllib.request](https://docs.python.org/3/library/urllib.request.html#module-urllib.request) |  Extensible library for opening URLs. | ? | 
| [urllib.response](https://docs.python.org/3/library/urllib.request.html#module-urllib.response) |  Response classes used by urllib. | ? | 
| [urllib.robotparser](https://docs.python.org/3/library/urllib.robotparser.html#module-urllib.robotparser) |  Load a robots.txt file and answer questions about fetchability of other URLs. | ? | 
| [uuid](https://docs.python.org/3/library/uuid.html#module-uuid) |  UUID objects (universally unique identifiers) according to RFC 4122 | ? | 
| [venv](https://docs.python.org/3/library/venv.html#module-venv) |  Creation of virtual environments. | ? | 
| [warnings](https://docs.python.org/3/library/warnings.html#module-warnings) |  Issue warning messages and control their disposition. | ✅ | [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/warnings)
| [wave](https://docs.python.org/3/library/wave.html#module-wave) |  Provide an interface to the WAV sound format. | ? | 
| [weakref](https://docs.python.org/3/library/weakref.html#module-weakref) |  Support for weak references and weak dictionaries. | ? | 
| [webbrowser](https://docs.python.org/3/library/webbrowser.html#module-webbrowser) |  Easy-to-use controller for Web browsers. | ? | 
| [winreg](https://docs.python.org/3/library/winreg.html#module-winreg) |  Routines and objects for manipulating the Windows registry. | ? | 
| [winsound](https://docs.python.org/3/library/winsound.html#module-winsound) |  Access to the sound-playing machinery for Windows. | ? | 
| [wsgiref](https://docs.python.org/3/library/wsgiref.html#module-wsgiref) |  WSGI Utilities and Reference Implementation. | ? | 
| [wsgiref.handlers](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.handlers) |  WSGI server/gateway base classes. | ? | 
| [wsgiref.headers](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.headers) |  WSGI response header tools. | ? | 
| [wsgiref.simple_server](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.simple_server) |  A simple WSGI HTTP server. | ? | 
| [wsgiref.util](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.util) |  WSGI environment utilities. | ? | 
| [wsgiref.validate](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.validate) |  WSGI conformance checker. | ? | 
| [xml](https://docs.python.org/3/library/xml.html#module-xml) |  Package containing XML processing modules | ? | 
| [xml.dom](https://docs.python.org/3/library/xml.dom.html#module-xml.dom) |  Document Object Model API for Python. | ? | 
| [xml.dom.minidom](https://docs.python.org/3/library/xml.dom.minidom.html#module-xml.dom.minidom) |  Minimal Document Object Model (DOM) implementation. | ? | 
| [xml.dom.pulldom](https://docs.python.org/3/library/xml.dom.pulldom.html#module-xml.dom.pulldom) |  Support for building partial DOM trees from SAX events. | ? | 
| [xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html#module-xml.etree.ElementTree) |  Implementation of the ElementTree API. | ? | 
| [xml.parsers.expat](https://docs.python.org/3/library/pyexpat.html#module-xml.parsers.expat) |  An interface to the Expat non-validating XML parser. | ? | 
| [xml.parsers.expat.errors](https://docs.python.org/3/library/pyexpat.html#module-xml.parsers.expat.errors) |   | ? | 
| [xml.parsers.expat.model](https://docs.python.org/3/library/pyexpat.html#module-xml.parsers.expat.model) |   | ? | 
| [xml.sax](https://docs.python.org/3/library/xml.sax.html#module-xml.sax) |  Package containing SAX2 base classes and convenience functions. | ? | 
| [xml.sax.handler](https://docs.python.org/3/library/xml.sax.handler.html#module-xml.sax.handler) |  Base classes for SAX event handlers. | ? | 
| [xml.sax.saxutils](https://docs.python.org/3/library/xml.sax.utils.html#module-xml.sax.saxutils) |  Convenience functions and classes for use with SAX. | ? | 
| [xml.sax.xmlreader](https://docs.python.org/3/library/xml.sax.reader.html#module-xml.sax.xmlreader) |  Interface which SAX-compliant XML parsers must implement. | ? | 
| xmlrpc |   | ? | 
| [xmlrpc.client](https://docs.python.org/3/library/xmlrpc.client.html#module-xmlrpc.client) |  XML-RPC client access. | ? | 
| [xmlrpc.server](https://docs.python.org/3/library/xmlrpc.server.html#module-xmlrpc.server) |  Basic XML-RPC server implementations. | ? | 
| [zipapp](https://docs.python.org/3/library/zipapp.html#module-zipapp) |  Manage executable Python zip archives | ? | 
| [zipfile](https://docs.python.org/3/library/zipfile.html#module-zipfile) |  Read and write ZIP-format archive files. | ? | 
| [zipimport](https://docs.python.org/3/library/zipimport.html#module-zipimport) |  Support for importing Python modules from ZIP archives. | ? | 
| [zlib](https://docs.python.org/3/library/zlib.html#module-zlib) |  Low-level interface to compression and decompression routines compatible with gzip. | ✅ | [built-in](https://docs.micropython.org/en/latest/library/uzlib.html)
| [zoneinfo](https://docs.python.org/3/library/zoneinfo.html#module-zoneinfo) |  IANA time zone support | ? | 
