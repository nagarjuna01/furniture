# quotes/views.
from django.apps import apps
from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction
from django.db.models import Q  
import logging
from quoting.revisions.revesion_snapshot import build_quote_snapshot
from accounts.mixins import TenantSafeMixin
from modular_calc.models import ModularProduct
from material.models.wood import WoodMaterial
from quoting.models import QuoteProduct,QuoteCommunication,QuotePartHardware,QuoteRevision,QuoteSolution,QuoteLineItem
from quoting.serializers import QuoteRevisionSerializer
from quoting.permissions import QuoteProductService
from quoting.services.bulk_expand import bulk_expand_products
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit
from django.shortcuts import render, get_object_or_404
from accounts.mixins import TenantSafeViewSetMixin
from products1.models import ProductBundle,ProductVariant
from .models import QuoteRequest, QuoteProduct, QuotePart, OverrideLog
from .serializers import (
    QuoteRequestSerializer,
    QuoteProductSerializer,
    QuoteCommunicationSerializer,
    QuoteWorkspaceSerializer,
    QuotePartSerializer,
    OverrideLogSerializer,
    MarketplaceQuoteSerializer,
    QuotePartHardwareSerializer,
    QuoteSolutionSerializer,
)
from quoting.services.recalculation import (
    recalc_quote_product,
    recalc_quote_solution,
    recalc_quote,
)
from quoting.pdf import QuotePDFSerializer

logger = logging.getLogger(__name__)

# views.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import QuoteProduct
from modular_calc.evaluation.product_engine import ProductEngine # Your Tier 5 Engine


    
    
# 1. MARKETPLACE CATALOG (Public Lead Generation)
# ---------------------------------------------------------
class MarketplaceCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = ModularProduct.objects.filter(is_public=True)


class QuoteRequestViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = QuoteRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuoteRequest.objects.filter(tenant=self.request.user.tenant).select_related("client", "tenant")
    
    @action(detail=True, methods=['post'])
    def add_solution(self, request, pk=None):
        quote_instance = self.get_object()
        name = request.data.get('name')

        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the solution linked to the current quote and tenant
        solution = QuoteSolution.objects.create(
        tenant=quote_instance.tenant, 
        quote=quote_instance,         
        name=name
    )
       
        return Response({
            'status': 'solution added', 
            'id': solution.id,
            'name': solution.name
        }, status=status.HTTP_201_CREATED)
  
    @action(detail=True, methods=['get'])
    def workspace(self, request, pk=None):
        """
        THE DISPATCHER: This solves your 404.
        Returns the 'Source of Truth' for the Alpine.js workspace.
        """
        quote = self.get_object()
        # We use a specialized serializer that nests Solutions -> Products -> Parts
        serializer = QuoteWorkspaceSerializer(quote) 
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='evaluate-product/(?P<product_id>[^/.]+)')
    @transaction.atomic
    def evaluate(self, request, pk=None, product_id=None):
        quote = self.get_object()
        # Ensure the product actually belongs to this quote (Tenant + Quote Safety)
        product = get_object_or_404(QuoteProduct, id=product_id, solution__quote=quote)
        
        # Map Alpine.js shorthand (l, w, h) to Model fields
        product.length_mm = request.data.get('l', product.length_mm)
        product.width_mm = request.data.get('w', product.width_mm)
        product.height_mm = request.data.get('h', product.height_mm)
        product.quantity = request.data.get('qty', product.quantity)
        product.save()

        try:
            # Step 1: Regenerate BOM
            QuoteProductService.expand_to_parts(product)
            # Step 2: Bubble up prices
            recalc_quote_product(product)
            recalc_quote_solution(product.solution)
            recalc_quote(quote)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=422)

        # Return the full workspace state so Alpine.js stays synced
        return Response(QuoteWorkspaceSerializer(quote).data)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        quote = self.get_object()

        if quote.status != "draft":
            return Response(
                {"detail": "Only draft quotes can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        quote.status = "approved"
        quote.approved_at = timezone.now()
        quote.approved_by = request.user
        quote.save(update_fields=["status", "approved_at", "approved_by"])

        return Response({"status": "approved"})

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def lock(self, request, pk=None):
        quote = (
            QuoteRequest.objects
            .select_for_update()
            .get(pk=pk, tenant=request.user.tenant)
        )

        if quote.status != "approved":
            return Response(
                {"detail": "Only approved quotes can be locked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        quote.status = "locked"
        quote.locked_at = timezone.now()
        quote.locked_by = request.user
        quote.save(update_fields=["status", "locked_at", "locked_by"])

        snapshot = build_quote_snapshot(quote)
        last_rev = (
            quote.revisions
            .select_for_update()
            .order_by("-revision_no")
            .first()
        )
        next_rev = (last_rev.revision_no + 1) if last_rev else 1

        QuoteRevision.objects.create(
            tenant=quote.tenant,
            quote=quote,
            revision_no=next_rev,
            snapshot=snapshot,
        )

        return Response({"status": "locked", "revision": next_rev})
    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        revision_no = request.query_params.get("revision")

        quote = QuoteRequest.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )

        if revision_no:
            revision = get_object_or_404(
                QuoteRevision,
                quote=quote,
                revision_no=revision_no,
            )
            data = revision.snapshot
            filename = f"Quote-{quote.quote_number}-R{revision_no}.pdf"
        else:
            if quote.status != "locked":
                return Response(
                    {"detail": "PDF allowed only for locked quotes"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = QuotePDFSerializer(quote).data
            filename = f"Quote-{quote.quote_number}.pdf"

        html = render_to_string(
            "quotes/pdf/quote_pdf.html",
            {"quote": data}
        )

        pdf = pdfkit.from_string(html, False)

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response
    @action(detail=True, methods=["get"])
    def diff(self, request, pk=None):
        revision = self.get_object()

        prev = (
            QuoteRevision.objects
            .filter(
                quote=revision.quote,
                revision_no__lt=revision.revision_no
            )
            .order_by("-revision_no")
            .first()
        )

        if not prev:
            return Response({"detail": "No previous revision"})

        diff = diff_revisions(
            prev.snapshot,
            revision.snapshot
        )

        return Response({
            "from": prev.revision_no,
            "to": revision.revision_no,
            "diff": diff,
        })
    
    @action(detail=False, methods=['get'], url_path='catalog-search')
    def catalog_search(self, request):
        # Filter Params
        mode = request.query_params.get('mode') # 'standard' or 'modular'
        cat_id = request.query_params.get('category')
        tier2 = request.query_params.get('tier2') # type (mod) or type (std)
        tier3 = request.query_params.get('tier3') # model (mod) or series (std)
        search_q = request.query_params.get('q')
        results = []

        if mode == 'modular':
            from modular_calc.models import ModularProduct
            qs = ModularProduct.objects.filter(tenant=request.user.tenant).prefetch_related(
                'parameters',
                'category',
                'type',
                'productmodel',
                'part_templates__material_whitelist__material',
                'part_templates__material_whitelist__edgeband_options__edgeband'
            )
            if cat_id: qs = qs.filter(category_id=cat_id)
            if tier2: qs = qs.filter(type_id=tier2)
            if tier3: qs = qs.filter(productmodel_id=tier3)
            
            for m in qs:
                material_map = {}                
                for pt in m.part_templates.all():
                    for mw in pt.material_whitelist.all():
                        mat = mw.material
                        if not mat:
                            continue
                        if mat.id not in material_map:
                            material_map[mat.id] = {
                                "id": mat.id,
                                "name": mat.name,
                                "edgebands": {}
                            }
                        
                        # Collect Edgebands (Nested loop fix)
                        for eb_opt in mw.edgeband_options.all():
                            eb = eb_opt.edgeband
                            if eb:
                                material_map[mat.id]["edgebands"][eb.id] = {
                                    "id": eb.id,
                                    "name": getattr(eb, "name", f"EB-{eb.id}")
                                }

                params = {p.abbreviation: float(p.default_value) for p in m.parameters.all()}
                
                results.append({
                    "id": str(m.id),
                    "is_modular": True,
                    "display_name": m.name,
                    "category_name": m.category.name if m.category else "N/A",
                    "type_name": m.type.name if m.type else "N/A",
                    "model_name": m.productmodel.name if m.productmodel else "N/A",
                    # Inputs
                    "l": params.get('L', 0), 
                    "w": params.get('W', 0), 
                    "h": params.get('H', 0),
                    # Material Handshake
                    "materials": [
                    {
                        "id": mat["id"],
                        "name": mat["name"],
                        "edgebands": list(mat["edgebands"].values())
                    }
                    for mat in material_map.values()
                ],
                            
                    "validation_logic": m.product_validation_expression,
                        })
        else:
            from products1.models import ProductVariant
            from django.db.models import Q

            # Select related to avoid N+1 queries on 20k variants
            qs = ProductVariant.objects.filter(
                product__tenant=request.user.tenant
            ).select_related(
                'product__product_type', 
                'product__product_series'
            )

            # 1. Hierarchy Filtering (The "True" filtering logic)
            if cat_id: 
                qs = qs.filter(product__product_type_id=cat_id)
            if tier2: 
                # This maps to 'product_series' in your JSON
                qs = qs.filter(product__product_series_id=tier2)

            # 2. Optimized Search (Optional but recommended)
            # If you removed the simple sku filter, use a complex one that hits Product Name OR Variant SKU
            if search_q:
                qs = qs.filter(
                    Q(product__name__icontains=search_q) | 
                    Q(sku__icontains=search_q)
                )

            for v in qs[:50]: # Enforce limit for UI performance
                results.append({
                    "variant_id": v.id,
                    "product_id": v.product.id,
                    "is_modular": False,
                    "product_name": v.product.name,
                    "product_type": v.product.product_type.name if v.product.product_type else "N/A",
                    "product_series": v.product.product_series.name if v.product.product_series else "N/A",
                    "display_name": f"{v.product.name} ({v.sku})",
                    "sku": v.sku,
                    "l": float(v.length or 0),
                    "w": float(v.width or 0),
                    "h": float(v.height or 0),
                    "base_price": float(v.selling_price or 0)
                })

        return Response(results)
    def build_quote_snapshot(quote):
        """
        Captures the entire state of the quote for audit/diffing.
        Explicitly handles Decimals to avoid JSON serialization errors.
        """
        from quoting.serializers import QuoteWorkspaceSerializer
        
        # We reuse the Workspace serializer to get the full tree
        serializer = QuoteWorkspaceSerializer(quote)
        data = serializer.data
        
        # Snapshot metadata for the record
        snapshot = {
            "metadata": {
                "captured_at": timezone.now().isoformat(),
                "quote_number": quote.quote_number,
                "grand_total": str(data['grand_total']), # String for precise decimals
            },
            "data": data
        }
        return snapshot
    @action(detail=False, methods=['get'], url_path='catalog-meta')
    def catalog_meta(self, request):
        from products1.models import ProductType, ProductSeries
        from modular_calc.models import ModularProductCategory, ModularProductType, ModularProductModel

        tenant = request.user.tenant

        # ---- STANDARD META ----
        standard_categories = ProductType.objects.filter(
            tenant=tenant
        ).values('id', 'name')

        standard_tier2 = ProductSeries.objects.filter(
            tenant=tenant
        ).values('id', 'name', 'product_type_id')

        # ---- MODULAR META ----
        modular_categories = ModularProductCategory.objects.filter(
            tenant=tenant
        ).values('id', 'name')

        modular_tier2 = ModularProductType.objects.filter(
            tenant=tenant
        ).values('id', 'name', 'category_id')

        modular_tier3 = ModularProductModel.objects.filter(
            tenant=tenant
        ).values('id', 'name', 'type_id')

        return Response({
            "standard": {
                "categories": list(standard_categories),
                "tier2": list(standard_tier2),
            },
            "modular": {
                "categories": list(modular_categories),
                "tier2": list(modular_tier2),
                "tier3": list(modular_tier3),
            }
        })
    def diff_revisions(old_snapshot, new_snapshot):
        """
        Compares two JSON snapshots to find price or dimension drifts.
        Output format: Technical JSON for evaluation.
        """
        diff_report = {
            "summary": {
                "old_total": old_snapshot['metadata']['grand_total'],
                "new_total": new_snapshot['metadata']['grand_total'],
            },
            "changes": []
        }
        
        # Create a map of products from the old snapshot
        old_products = {p['id']: p for s in old_snapshot['data']['solutions'] for p in s['items']}
        new_products = {p['id']: p for s in new_snapshot['data']['solutions'] for p in s['items']}

        for pid, new_p in new_products.items():
            if pid in old_products:
                old_p = old_products[pid]
                # Check for Dimension or Price drift
                if (old_p['l'] != new_p['l'] or old_p['w'] != new_p['w'] or old_p['h'] != new_p['h']):
                    diff_report['changes'].append({
                        "product_id": pid,
                        "name": new_p['product_name'],
                        "type": "DIMENSION_CHANGE",
                        "from": f"{old_p['l']}x{old_p['w']}x{old_p['h']}",
                        "to": f"{new_p['l']}x{new_p['w']}x{new_p['h']}"
                    })
        
        return diff_report    
        
class QuoteProductViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return (
            QuoteProduct.objects
            .filter(tenant=self.request.user.tenant)
            .select_related(
                "solution",
                "solution__quote",
                "product_template",
                "override_material",
            )
            .prefetch_related(
                "parts__material",
                "parts__hardware__hardware",
            )
        )
    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuoteWorkspaceSerializer
        return QuoteProductSerializer
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        qty = serializer.validated_data.get('quantity') or request.data.get('quantity') or 1
        qty = int(qty) # Force integer to avoid math errors
        is_modular = data.get('modular_product') is not None

        if is_modular:
            # MODULAR PATH: Engine handles complex CP/SP math
            engine_payload = {
                "product": data['modular_product'],
                "product_dims": {"L": data['length_mm'], "W": data['width_mm'], "H": data['height_mm']},
                "selected_material_id": request.data.get('material_id'),
                "quantities": [data.get('quantity', 1)]
            }

            engine = ProductEngine(engine_payload)
            engine_result = engine.run() 
            
            # Tier 5 Integrity: Save both calculated prices
            instance = serializer.save(
                tenant=request.user.tenant,
                unit_cp=engine_result['pricing']['total_cost_price'],
                unit_sp=engine_result['pricing']['final_selling_price'],
                is_modular=True,
                engine_snapshot=engine_result 
            )
        else:
            # STANDARD PATH: Map directly from Variant
            variant = data.get('product_variant')
            unit_cp=variant.purchase_price if variant else 0 # Standard CP
            unit_sp=variant.selling_price if variant else 0  # Standard SP
            calc_cp = unit_cp * qty
            calc_sp = unit_sp * qty
            instance = serializer.save(
                tenant=request.user.tenant,
                product_template=data.get('product_template'),
                product_variant=variant,
                total_cp=calc_cp,
                total_sp=calc_sp,
                source_type="template"
            )
        
        recalc_quote_product(instance) 
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def evaluate(self, request, pk=None):
        qp = self.get_object()
        return Response(QuoteProductService.evaluate(qp))

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def expand(self, request, pk=None):
        qp = QuoteProductService.expand_to_parts(self.get_object())
        return Response(self.get_serializer(qp).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def freeze(self, request, pk=None):
        qp = QuoteProductService.freeze(self.get_object())

        recalc_quote_product(qp)
        recalc_quote_solution(qp.solution)
        recalc_quote(qp.solution.quote)

        return Response(self.get_serializer(qp).data)
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_expand(self, request):
        ids = request.data.get("product_ids", [])

        qs = self.get_queryset().filter(id__in=ids)
        expanded = bulk_expand_products(list(qs))

        serializer = QuoteProductSerializer(expanded, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_freeze(self, request):
        ids = request.data.get("product_ids", [])
        products = self.get_queryset().filter(id__in=ids)

        frozen = []
        skipped = []

        for qp in products.select_for_update():
            if qp.is_frozen:
                skipped.append(qp.id)
                continue

            QuoteProductService.freeze(qp)
            frozen.append(qp.id)

        return Response({
            "frozen": frozen,
            "skipped": skipped,
        })
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_recalc(self, request):
        ids = request.data.get("product_ids", [])
        products = self.get_queryset().filter(id__in=ids)

        affected_quotes = set()

        for qp in products:
            recalc_quote_product(qp)
            affected_quotes.add(qp.solution.quote_id)

        for qid in affected_quotes:
            recalc_quote(qid)

        return Response({"status": "recalculated"})


class QuotePartViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    # Use the unified serializer we defined earlier
    serializer_class = QuotePartSerializer 

    def get_queryset(self):
        user = self.request.user
        # Ensure we don't leak data across tenants
        return (
            QuotePart.objects
            .filter(tenant=user.tenant)
            .select_related(
                "quote_product",
                "material",
            )
            .prefetch_related("hardware__hardware")
        )

class OverrideLogViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    """
    Audit Trail ViewSet. 
    Tracks manual price/dimension overrides that bypass the Handshake logic.
    """
    serializer_class = OverrideLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TenantSafeViewSetMixin likely provides self.request.tenant
        # We optimize with select_related to avoid N+1 on 'changed_by'
        return (
            OverrideLog.objects
            .filter(tenant=self.request.user.tenant)
            .select_related("changed_by")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        # Auto-bind the tenant and the user performing the override
        serializer.save(
            tenant=self.request.user.tenant,
            changed_by=self.request.user
        )


class QuoteCommunicationViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = QuoteCommunicationSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return QuoteCommunication.objects.none()

        if user.is_superuser:
            return QuoteCommunication.objects.all()

        return QuoteCommunication.objects.filter(tenant=user.tenant)


    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            sent_by=self.request.user
        )

class QuoteRevisionViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = QuoteRevisionSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return QuoteRevision.objects.none()
        if user.is_superuser:
            return QuoteRevision.objects.all()
        return QuoteRevision.objects.filter(tenant=user.tenant)

class MarketplaceQuoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public ViewSet for lead generation.
    Allows anyone to see products marked as 'is_public'.
    """
    serializer_class = MarketplaceQuoteSerializer
    permission_classes = [AllowAny] # No tenant check here

    def get_queryset(self):
        return (
            QuoteProduct.objects
            .filter(
                product_template__is_public=True,
                quote__status="draft" # Only show active public drafts
            )
            .select_related("quote", "product_template", "product_template__category")
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Custom retrieve to handle historical revision viewing 
        via the specialized resolver.
        """
        instance = self.get_object()
        revision_no = request.query_params.get("revision")
        
        # If no revision, just return standard serialized data
        if not revision_no:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
            
        # If revision requested, use the snapshot resolver
        from quoting.services.snapshots.resolver import resolve_quote_view
        payload = resolve_quote_view(instance.quote, revision_no)
        return Response(payload)
    
class QuotePartHardwareViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    """
    BOM Hardware ViewSet.
    Managed primarily via the QuotePart expansion service.
    """
    serializer_class = QuotePartHardwareSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            QuotePartHardware.objects
            .filter(tenant=self.request.user.tenant)
            .select_related("hardware", "quote_part")
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)

# quotes/views.py
class QuoteSolutionViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    """
    Handles the Zone/Room layer of the Quotation.
    Supports PATCH for renaming and DELETE for removing zones.
    """
    serializer_class = QuoteSolutionSerializer
    
    def get_queryset(self):
        # Explicit tenant isolation via the mixin or manual filter
        return QuoteSolution.objects.filter(tenant=self.request.user.tenant)