from django import forms
from django.forms import formset_factory, modelformset_factory,BaseModelFormSet
from .models import Part1
from material.models import EdgeBand,WoodEn
import logging
logger = logging.getLogger(__name__)

class ConstraintForm(forms.Form):
    abbreviation = forms.CharField(max_length=20)
    value = forms.DecimalField(decimal_places=2)

ConstraintFormSet = formset_factory(ConstraintForm, extra=3)


class PartForm(forms.ModelForm):
    class Meta:
        model = Part1
        fields = [
            'name',
            'part_length_equation',
            'part_width_equation',
            'part_qty_equation',
            'part_material',
            'part_edgematerial_top',
            'part_edgematerial_left',
            'part_edgematerial_right',
            'part_edgematerial_bottom',
            'part_shape',
            'grain_direction',
            'shape_wastage_multiplier',
        ]

    def __init__(self, *args, compatible_edgebands=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Start with empty queryset for edges
        for field in ['part_edgematerial_top', 'part_edgematerial_left', 'part_edgematerial_right', 'part_edgematerial_bottom']:
            self.fields[field].queryset = EdgeBand.objects.none()

        # If compatible edgebands passed, assign to edge fields
        if compatible_edgebands is not None:
            for field in ['part_edgematerial_top', 'part_edgematerial_left', 'part_edgematerial_right', 'part_edgematerial_bottom']:
                self.fields[field].queryset = compatible_edgebands

DEFAULT_MATERIAL_ID = 1
class BasePartFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for form in self.forms:
            material_id = None

            if self.is_bound:
                material_id = form.data.get(f'{form.prefix}-part_material')
            if not material_id:
                material_id = form.initial.get('part_material') or getattr(form.instance, 'part_material_id', None)

            if not material_id:
                material_id = DEFAULT_MATERIAL_ID  # fallback to default

            compatible_edgebands = EdgeBand.objects.none()
            if material_id:
                try:
                    material = WoodEn.objects.get(pk=material_id)
                    compatible_edgebands = material.compatible_edgebands.all()
                except WoodEn.DoesNotExist:
                    pass
                print(f"Material ID: {material_id} - Compatible edges: {compatible_edgebands.count()}")

            form.__init__(
                form.data if self.is_bound else None,
                prefix=form.prefix,
                compatible_edgebands=compatible_edgebands,
                instance=form.instance,
            )

PartFormSet = modelformset_factory(
    Part1,
    form=PartForm,
    formset=BasePartFormSet,
    extra=3,
    can_delete=True,
)