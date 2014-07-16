from django.contrib.sites.models import RequestSite
from django.template.defaulttags import URLNode
from django import template
from django.template.base import TemplateSyntaxError, kwarg_re

register = template.Library()

class AbsoluteUrlNode(URLNode):
    def __init__(self, viewname, args, kwargs, asvar):
        super().__init__(viewname, args, kwargs, False)
        self.asvar_absolute = asvar

    def render(self, context):
        url = super().render(context)
        request = context['request']
        absolute = RequestSite(request).domain
        if request.is_secure():
            protocol = 'https'
        else:
            protocol = 'http'

        absolute_url = protocol + '://' + absolute + url
        if self.asvar_absolute:
            context[self.asvar_absolute] = absolute_url
            return ''
        else:
            return absolute_url

@register.tag()
def absoluteurl(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    try:
        viewname = parser.compile_filter(bits[1])
    except TemplateSyntaxError as exc:
        exc.args = (exc.args[0] + ". "
                "The syntax of 'url' changed in Django 1.5, see the docs."),
        raise
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return AbsoluteUrlNode(viewname, args, kwargs, asvar)