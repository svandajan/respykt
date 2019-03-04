# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1551611450.6514652
_enable_loop = True
_template_filename = '../docs/templates/article.html'
_template_uri = 'article.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        loop = __M_loop = runtime.LoopStack()
        authors = context.get('authors', UNDEFINED)
        len = context.get('len', UNDEFINED)
        date = context.get('date', UNDEFINED)
        header_image_src = context.get('header_image_src', UNDEFINED)
        category = context.get('category', UNDEFINED)
        topics = context.get('topics', UNDEFINED)
        content = context.get('content', UNDEFINED)
        title = context.get('title', UNDEFINED)
        subtitle = context.get('subtitle', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE html>\r\n<html>\r\n<head>\r\n    <meta charset="UTF-8">\r\n    <link rel="stylesheet" href="../docs/static/style.css" type="text/css"/>\r\n    <title>')
        __M_writer(str(title))
        __M_writer('</title>\r\n</head>\r\n<body>\r\n<div class="header">\r\n    <h1 id="header-title">')
        __M_writer(str(title))
        __M_writer('</h1>\r\n    <h2 id="header-subtitle">')
        __M_writer(str(subtitle))
        __M_writer('</h2>\r\n    <div class="category">')
        __M_writer(str(category))
        __M_writer('</div>\r\n    <div class="topics">\r\n')
        loop = __M_loop._enter(topics)
        try:
            for c in loop:
                __M_writer('        <span class="topic-name">')
                __M_writer(str(c))
                __M_writer('</span>\r\n')
                if loop.index < len(topics) - 1:
                    __M_writer('        <span class="topic-delim"> &diams; </span>\r\n')
        finally:
            loop = __M_loop._exit()
        __M_writer('    </div>\r\n')
        if header_image_src is not None:
            __M_writer('    <img class="header-image" src="')
            __M_writer(str(header_image_src))
            __M_writer('"/>\r\n')
        __M_writer('    <div class="authors">')
        __M_writer(str(authors))
        __M_writer('</div>\r\n    <div class="date">')
        __M_writer(str(date))
        __M_writer('</div>\r\n</div>\r\n')
        __M_writer(str(content))
        __M_writer('\r\n</body>\r\n</html>')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "../docs/templates/article.html", "uri": "article.html", "source_encoding": "ascii", "line_map": {"16": 0, "31": 1, "32": 6, "33": 6, "34": 10, "35": 10, "36": 11, "37": 11, "38": 12, "39": 12, "40": 14, "43": 15, "44": 15, "45": 15, "46": 16, "47": 17, "50": 20, "51": 21, "52": 22, "53": 22, "54": 22, "55": 24, "56": 24, "57": 24, "58": 25, "59": 25, "60": 27, "61": 27, "67": 61}}
__M_END_METADATA
"""
