from django.forms import ValidationError
from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
import uuid
from rest_framework.exceptions import NotFound

from .models import (
    ModularProduct, PartTemplate,
    PartMaterialWhitelist, PartEdgeBandWhitelist,
    PartHardwareRule
)
from .serializers import (
    ModularProductSerializer, PartTemplateSerializer,
    PartMaterialWhitelistSerializer, PartEdgeBandWhitelistSerializer,
    PartHardwareRuleSerializer
)


class ModularProductViewSet(viewsets.ModelViewSet):
    queryset = ModularProduct.objects.all()
    serializer_class = ModularProductSerializer
    #permission_classes = [IsAuthenticated]

    # ✅ UUID-safe lookup
    lookup_field = "id"
    lookup_value_regex = "[0-9a-f-]{36}"

class PartTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = PartTemplateSerializer
    queryset = PartTemplate.objects.all()

    def get_queryset(self):
        product_pk = self.kwargs.get("product_pk")
        qs = super().get_queryset()
        if product_pk:
            qs = qs.filter(product_id=product_pk)
        return qs

    def perform_create(self, serializer):
        print("KWARGS DEBUG =>", self.kwargs)  # 👀
        product_id = (
            self.kwargs.get("product_pk") or
            self.kwargs.get("id_pk") or
            self.kwargs.get("modularproduct_pk") or
            self.kwargs.get("product_id")  # ✅ added this
        )
        if not product_id:
            raise ValidationError("Missing product_id in URL.")
        serializer.save(product_id=product_id)




class PartMaterialWhitelistViewSet(viewsets.ModelViewSet):
    queryset = PartMaterialWhitelist.objects.select_related("part_template", "material").all()
    serializer_class = PartMaterialWhitelistSerializer


class PartEdgeBandWhitelistViewSet(viewsets.ModelViewSet):
    queryset = PartEdgeBandWhitelist.objects.select_related("part_template", "edgeband").all()
    serializer_class = PartEdgeBandWhitelistSerializer


class PartHardwareRuleViewSet(viewsets.ModelViewSet):
    queryset = PartHardwareRule.objects.select_related("part_template", "hardware").all()
    serializer_class = PartHardwareRuleSerializer

def modular(request):
    return render(request, 'modular0826.html')