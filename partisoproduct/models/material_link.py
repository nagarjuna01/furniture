from django.db import models
from material.models.edgeband import EdgeBand
from material.models.category import Category,CategoryModel,CategoryTypes
from material.models.wood import WoodMaterial
from .modular import Modular1

GRAIN_CHOICES = [
    ('none', 'None'),
    ('horizontal', 'Horizontal'),
    ('vertical', 'Vertical'),
]

class Part1(models.Model):
    name = models.CharField(max_length=255)
    modular_product = models.ForeignKey(Modular1, on_delete=models.CASCADE, related_name='parts')

    part_length_equation = models.CharField(max_length=255)
    part_width_equation = models.CharField(max_length=255)
    part_qty_equation = models.CharField(max_length=255)

    compatible_categories = models.ManyToManyField(
    'material.Category', blank=True, related_name='parts_by_category'
    )
    compatible_types = models.ManyToManyField(
        'material.CategoryTypes', blank=True, related_name='parts_by_type'
    )
    compatible_models = models.ManyToManyField(
        'material.CategoryModel', blank=True, related_name='parts_by_model'
    )
    compatible_woods = models.ManyToManyField(
        'material.WoodMaterial', blank=True, related_name='parts_by_wood'
    )

    part_edgematerial_top = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name='part_top_edges')
    part_edgematerial_left = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name='part_left_edges')
    part_edgematerial_right = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name='part_right_edges')
    part_edgematerial_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name='part_bottom_edges')
    part_shape = models.CharField(
        max_length=50,
        choices=[
            ('rectangle', 'Rectangle'),
            ('circle', 'Circle'),
            ('curvilinear', 'Curvilinear'),
            ('l_shape', 'L Shape'),
            ('triangle', 'Triangle'),
        ],
        default='rectangle'
    )

    grain_direction = models.CharField(max_length=20, choices=GRAIN_CHOICES, default='none')
    part_dimensions = models.JSONField(default=dict)
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    hardware_total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hardware_total_sell = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
