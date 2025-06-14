"""
Base form mixin to apply Dason/Bootstrap widget classes.
"""
class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get('class', '')
            if 'form-control' not in css_class:
                field.widget.attrs['class'] = (css_class + ' form-control').strip()
