# material/views.py


from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models.tenant import Tenant
from accounts.mixins import TenantSafeViewSetMixin

from material.models.brand import Brand
from material.models.units import MeasurementUnit, BillingUnit
from material.models.category import Category, CategoryTypes, CategoryModel
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand, EdgebandName
from material.models.hardware import Hardware, HardwareGroup

from material.serializers import (
    BrandSerializer,
    MeasurementUnitSerializer,
    BillingUnitSerializer,
    CategorySerializer,
    CategoryTypesSerializer,
    CategoryModelSerializer,
    WoodMaterialSerializer,
    EdgeBandSerializer,
    EdgebandNameSerializer,
    HardwareSerializer,
    HardwareGroupSerializer,
)

# ---------------------------------------------------------
# TEMPLATE VIEWS
# ---------------------------------------------------------

@login_required(login_url="/accounts/login/")
def brand_list_page(request):
    return render(request, "brand_management.html")


@login_required(login_url="/accounts/login/")
def hardware_view(request):
    return render(request, "hardware_list.html")

def brand_list_alpine(request):
    return render(request,"brand_alpine.html")

@login_required(login_url="/accounts/login/")
def edgeband_list(request):
    return render(request, "edgeband_list_copy.html")


@login_required(login_url="/accounts/login/")
def category_browser(request):
    return render(request, "categorybrowser_copy.html")


@login_required
def measurement_unit_view(request):
    return render(request, "measurementunit.html", {})


@login_required
def billing_unit_view(request):
    return render(request, "billingunit.html", {})


# ---------------------------------------------------------
# API VIEWSETS
# ---------------------------------------------------------

class BrandViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class WoodMaterialViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = WoodMaterial.objects.all()
    serializer_class = WoodMaterialSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "material_grp",
            "material_type",
            "material_model",
            "brand",
            "cost_unit",
            "sell_unit",
        )

        params = self.request.query_params

        # ✅ HIERARCHICAL FILTERING (FIXED)
        if params.get("material_grp"):
            qs = qs.filter(material_grp_id=params["material_grp"])

        if params.get("material_type"):
            qs = qs.filter(material_type_id=params["material_type"])

        if params.get("material_model"):
            qs = qs.filter(material_model_id=params["material_model"])

        # ✅ OPTIONAL FILTERS
        if params.get("brand"):
            qs = qs.filter(brand_id=params["brand"])

        if params.get("thickness"):
            qs = qs.filter(thickness_value=params["thickness"])
        if params.get("grain"):
            qs = qs.filter(grain=params("grain"))


        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.is_active:
            return Response(
                {"detail": "Deactivate material before deletion."},
                status=400
            )

        return super().destroy(request, *args, **kwargs)
    
class EdgeBandViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = EdgeBand.objects.all()
    serializer_class = EdgeBandSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["edgeband_name__name"]
    ordering_fields = ["cost_price", "sell_price"]

    filterset_fields = {
        "edgeband_name": ["exact"],
        "edgeband_name__brand": ["exact"],
        "thickness": ["exact", "gte", "lte"],
        "cost_price": ["gte", "lte"],
        "sell_price": ["gte", "lte"],
    }

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
    # def get_queryset(self):
    #     qs = EdgeBand.objects.all()
    #     is_active = self.request.query_params.get("is_active")
    #     if is_active is not None:
    #         if is_active.lower() in ["true", "1"]:
    #             qs = qs.filter(is_active=True)
    #         elif is_active.lower() in ["false", "0"]:
    #             qs = qs.filter(is_active=False)
    #     else:
    #         qs = qs.filter(is_active=True)  # default
    #     return qs

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        instance = self.get_object()
        data = EdgeBandSerializer(instance).data
        data.pop("id", None)

        serializer = EdgeBandSerializer(
            data=data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        new_obj = serializer.save()

        return Response(
            EdgeBandSerializer(new_obj).data,
            status=status.HTTP_201_CREATED
        )

class HardwareGroupViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = HardwareGroup.objects.all()
    serializer_class = HardwareGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "is_active"]

class HardwareViewSet(TenantSafeViewSetMixin, ModelViewSet):
    serializer_class = HardwareSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "h_name",
        "brand__name",
        "h_group__name",
    ]

    ordering_fields = [
        "cost_price",
        "sell_price",
        "h_name",
    ]

    def get_queryset(self):
        qs = (
            Hardware.objects
            .select_related("h_group", "brand", "billing_unit")
        )

        # 🔐 tenant handled by TenantSafeViewSetMixin

        # ✅ list view → only active
        if self.action == "list":
            qs = qs.filter(is_active=True)

        return qs

    # ✅ SOFT DELETE
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

class MeasurementUnitViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class BillingUnitViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = BillingUnit.objects.all()
    serializer_class = BillingUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "factor"]

class CategoryViewSet(TenantSafeViewSetMixin,ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        qs = Category.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(tenant=self.request.user.tenant)
        return qs.order_by("name")

    @transaction.atomic
    def perform_destroy(self, instance):
        # soft delete pattern if needed
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class CategoryTypesViewSet(ModelViewSet):
    serializer_class = CategoryTypesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        qs = CategoryTypes.objects.select_related("category")
        if not self.request.user.is_superuser:
            qs = qs.filter(category__tenant=self.request.user.tenant)
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs.order_by("name")

    @transaction.atomic
    def perform_destroy(self, instance):
        if instance.models.exists():
            return Response(
                {"detail": "This CategoryType has models. Cannot delete."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()


class CategoryModelViewSet(ModelViewSet):
    serializer_class = CategoryModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        qs = CategoryModel.objects.select_related(
            "model_category",
            "model_category__category",
        )
        if not self.request.user.is_superuser:
            qs = qs.filter(model_category__category__tenant=self.request.user.tenant)
        model_category_id = self.request.query_params.get("model_category")
        if model_category_id:
            qs = qs.filter(model_category_id=model_category_id)
        return qs.order_by("name")

    @transaction.atomic
    def perform_destroy(self, instance):
        # If you have dependent objects like WoodMaterial, you can block delete
        instance.delete()

class EdgebandNameViewSet(ModelViewSet):
    queryset = EdgebandName.objects.all()
    serializer_class = EdgebandNameSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.edgebands.exists():
            return Response(
                {"detail": "This EdgeBand Name is in use."}, status=400
            )
        return super().destroy(request, *args, **kwargs)
