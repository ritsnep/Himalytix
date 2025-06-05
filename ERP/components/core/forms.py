from typing import Any, Dict, List, Optional, Type, Union

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.forms.widgets import Media


class DynamicFormMixin:
    """
    Mixin that adds dynamic field configuration capabilities to forms.
    """
    def __init__(self, *args, **kwargs):
        # Extract field configuration before calling parent __init__
        self.field_config = kwargs.pop('field_config', {})
        super().__init__(*args, **kwargs)
        self.configure_fields()

    def configure_fields(self):
        """Configure form fields based on field_config."""
        for field_name, config in self.field_config.items():
            if field_name in self.fields:
                field = self.fields[field_name]
                
                # Apply enabled/disabled state
                if 'enabled' in config:
                    field.disabled = not config['enabled']
                
                # Apply custom validation
                if 'validators' in config:
                    field.validators.extend(config['validators'])
                
                # Apply widget attributes
                if 'widget_attrs' in config:
                    field.widget.attrs.update(config['widget_attrs'])
                    
                # Apply custom CSS classes
                if 'css_classes' in config:
                    classes = field.widget.attrs.get('class', '').split()
                    classes.extend(config['css_classes'])
                    field.widget.attrs['class'] = ' '.join(classes)

    def add_field(self, name: str, field: forms.Field, config: Optional[Dict] = None):
        """Dynamically add a new field to the form."""
        self.fields[name] = field
        if config:
            self.field_config[name] = config
            self.configure_fields()

    def remove_field(self, name: str):
        """Remove a field from the form."""
        if name in self.fields:
            del self.fields[name]
            if name in self.field_config:
                del self.field_config[name]

    def get_layout(self) -> List[Dict]:
        """Get the form layout configuration."""
        return getattr(self, 'layout', [])


class DynamicForm(DynamicFormMixin, forms.Form):
    """Base form class with dynamic field configuration."""
    pass


class DynamicModelForm(DynamicFormMixin, ModelForm):
    """Model form with dynamic field configuration."""
    pass


class FormFieldConfigBuilder:
    """Helper class to build field configurations."""
    def __init__(self):
        self.config = {}

    def set_enabled(self, enabled: bool = True):
        self.config['enabled'] = enabled
        return self

    def add_validator(self, validator_func):
        if 'validators' not in self.config:
            self.config['validators'] = []
        self.config['validators'].append(validator_func)
        return self

    def set_widget_attrs(self, attrs: Dict):
        if 'widget_attrs' not in self.config:
            self.config['widget_attrs'] = {}
        self.config['widget_attrs'].update(attrs)
        return self

    def add_css_classes(self, *classes):
        if 'css_classes' not in self.config:
            self.config['css_classes'] = []
        self.config['css_classes'].extend(classes)
        return self

    def build(self) -> Dict:
        return self.config
