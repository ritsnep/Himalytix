from django.core.management.base import BaseCommand
from django.apps import apps
from usermanagement.models import Module, Entity, Permission

class Command(BaseCommand):
    help = 'Generates permissions for all models in the system'

    def handle(self, *args, **kwargs):
        # Get all installed apps
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('ERP.'):
                module_name = app_config.label
                module, _ = Module.objects.get_or_create(
                    name=module_name.title(),
                    description=f'Module for {module_name}'
                )

                # Get all models in the app
                for model in app_config.get_models():
                    if model._meta.abstract:
                        continue

                    entity_name = model._meta.model_name
                    entity, _ = Entity.objects.get_or_create(
                        module=module,
                        name=entity_name.title(),
                        description=f'Entity for {entity_name}'
                    )

                    # Create CRUD permissions
                    actions = ['view', 'add', 'change', 'delete']
                    for action in actions:
                        Permission.objects.get_or_create(
                            name=f'Can {action} {entity_name}',
                            codename=f'{module_name}_{entity_name}_{action}',
                            description=f'Can {action} {entity_name}',
                            module=module,
                            entity=entity,
                            action=action
                        )

        self.stdout.write(self.style.SUCCESS('Successfully generated permissions')) 