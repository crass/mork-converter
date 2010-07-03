# Copyright (c) 2009 Kevin Goodsell

# Output filter for writing Mork databases in XML format. This is also a basic
# introduction to writing output filters using the tools in output.util.
#
# For reference, the XML 1.0 specification is available here:
# http://www.w3.org/TR/2008/REC-xml-20081126/

import re
import warnings
import codecs

import MorkDB.filter.util as util

# REQUIRED: All output filters should include _MORK_OUTPUT_FILTER. The value
# doesn't matter, just the presence of the variable.
_MORK_OUTPUT_FILTER = True

# REQUIRED: All output filters should have a description. It is displayed in
# the help output, unless it evaluates as false.
description = 'Simple XML output filter'

# REQUIRED: All output filters have a usage. This is a sequence of items,
# and each item is a sequence of two items. Effectively this is a sequence of
# (argumentName, argumentDescription) pairs. util.Argument behaves as a
# sequence of two items, but can also have a 'converter', which is used in
# util.convertArgs to convert the argument text (a string) to whatever type
# is desired. When not supplied, the argument just remains a string.
usage = [
    util.Argument('out', 'Name to use for output file (default: mork.xml)'),
]

# REQUIRED: The output function does the real work. Its arguments are a
# MorkDatabase instance and a dict of arguments with argument names for the
# keys and argument text for the values.
def output(db, args):
    # convertArgs uses the names in 'usage' to check the validity of the
    # arguments and uses the converters in 'usage' to convert argument text
    # to more useful types.
    #
    # This does NOT check for required arguments. If there are required args,
    # check for them specifically.
    args = util.convertArgs(usage, args)
    return _outputHelper(db, **args)

_indentStr = '    '

def _outputHelper(db, out='mork.xml'):
    f = codecs.open(out, 'w', encoding='utf-8')
    print >> f, '<?xml version="1.0" encoding="UTF-8" ?>'
    print >> f, '<morkxml>'

    for (namespace, oid, table) in db.tables.items():
        meta = db.metaTables.get((namespace, oid))
        _writeTable(f, namespace, oid, table, meta)

    print >> f, '</morkxml>'
    f.close()

def _writeTable(f, namespace, oid, table, meta=None, indent=1):
    indentStr = _indentStr * indent
    print >> f, '%s<table namespace=%s id=%s>' % (indentStr,
        _formatAttribute(namespace), _formatAttribute(oid))

    for (rowNamespace, rowId, row) in table:
        _writeRow(f, rowNamespace, rowId, row, indent + 1)

    if meta is not None:
        _writeMetaTable(f, meta, indent + 1)

    print >> f, '%s</table>' % indentStr

def _writeMetaTable(f, meta, indent):
    indentStr = _indentStr * indent
    print >> f, '%s<metatable>' % indentStr

    for (column, value) in meta.cells.items():
        _writeCell(f, column, value, indent + 1)

    for (namespace, oid, row) in meta.rows:
        _writeRow(f, namespace, oid, row, indent + 1)

    print >> f, '%s</metatable>' % indentStr

def _writeRow(f, namespace, oid, row, indent):
    indentStr = _indentStr * indent
    print >> f, '%s<row namespace=%s id=%s>' % (indentStr,
        _formatAttribute(namespace), _formatAttribute(oid))

    for (column, value) in row.items():
        _writeCell(f, column, value, indent + 1)

    print >> f, '%s</row>' % indentStr

def _writeCell(f, column, value, indent):
    indentStr = _indentStr * indent
    print >> f, '%s<cell column=%s>%s</cell>' % (indentStr,
        _formatAttribute(column), _formatElementText(value))

# Regex for stuff that's not in the 'Char' production of the XML grammar
_non_char = (
    u'['
    u'\x00-\x08\x0B\x0C\x0E-\x1F'  # Control characters
    u'\uD800-\uDFFF'               # Surrogates
    u'\uFFFE\uFFFF'                # Permanently unassigned (BOM)
    u']'
)

# Regex for stuff that's not in the 'AttValue' production in the XML grammar
_non_att_value_matcher = re.compile(_non_char + u'|[<&"]')

# Regex for stuff that's not in the 'CharData' production in the XML grammar
_non_char_data_matcher = re.compile(_non_char + u'|[<&]|]]>')

_replacements = {
    '<'   : '&lt;',
    '>'   : '&gt;',
    '&'   : '&amp;',
    '"'   : '&quot;',
    "'"   : '&apos;',
    ']]>' : ']]&gt;',
}
def _replacer(match):
    old = match.group()
    new = _replacements.get(old)
    if new is None:
        warnings.warn('found invalid XML characters; this will not be a '
                      'well-formed XML document')
        # Use a CharRef even though it's not well-formed, since CharRefs don't
        # get around the character limitations in XML.
        new = '&#x%x;' % ord(old)

    return new

def _formatAttribute(value):
    # This corresponds to 'AttValue' in the spec.
    return '"%s"' % _non_att_value_matcher.sub(_replacer, value)

def _formatElementText(value):
    # This correspond to 'CharData' in the spec.
    return _non_char_data_matcher.sub(_replacer, value)
