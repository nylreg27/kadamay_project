# apps/common/mixins.py

class StyledFormMixin:
    def apply_tailwind_styles(self):
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            tailwind_base = 'w-full p-2 border border-gray-300 rounded bg-white text-gray-900'
            field.widget.attrs['class'] = f"{existing_classes} {tailwind_base}".strip(
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_styles()
