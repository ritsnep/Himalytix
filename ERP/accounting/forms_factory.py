from django import forms
from .models import ChartOfAccount, Department, Project, CostCenter
from typing import Type

FIELD_MAP = {
    "char": forms.CharField,
    "text": lambda **kw: forms.CharField(widget=forms.Textarea, **kw),
    "date": forms.DateField,
    "decimal": lambda **kw: forms.DecimalField(max_digits=19, decimal_places=4, **kw),
    "account": lambda **kw: forms.ModelChoiceField(queryset=ChartOfAccount.objects.none(), **kw),
    "department": lambda **kw: forms.ModelChoiceField(queryset=Department.objects.none(), **kw),
    "project": lambda **kw: forms.ModelChoiceField(queryset=Project.objects.none(), **kw),
    "cost_center": lambda **kw: forms.ModelChoiceField(queryset=CostCenter.objects.none(), **kw),
}

def build_form(schema: dict, *, organization, prefix="dynamic", model=None) -> Type[forms.ModelForm]:
    """Return a concrete ModelForm subclass based on a ui_schema dict."""
    attrs = {}
    fields = []
    if not schema and model:
        # If schema is empty, use all model fields except id/pk and non-editable fields
        for field in model._meta.fields:
            if field.name in ['id', 'pk']:
                continue
            if not getattr(field, 'editable', True):
                continue
            attrs[field.name] = forms.CharField(required=not field.blank)
            fields.append(field.name)
    else:
        for name, spec in schema.items():
            field_type = FIELD_MAP[spec["type"]]
            kwargs = spec.get("kwargs", {})
            required = spec.get("required", True)
            attrs[name] = field_type(required=required, **kwargs)
            fields.append(name)
            # org-scoped queryset hook
            if spec["type"] in {"account", "department", "project", "cost_center"}:
                attrs[name].queryset = attrs[name].queryset.model.objects.filter(organization=organization)
    # Define Meta class dynamically
    Meta = type("Meta", (), {"model": model, "fields": fields})
    attrs['Meta'] = Meta
    return type(f"{prefix.title()}ModelForm", (forms.ModelForm,), attrs) 