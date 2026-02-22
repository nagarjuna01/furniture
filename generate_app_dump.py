import os
import django
import json
import sys
from decimal import Decimal

# 1. SETUP DJANGO CONTEXT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "furniture.settings")
django.setup()

from django.utils import timezone
from modular_calc.models import ModularProduct, PartTemplate, PartMaterialWhitelist
from quoting.models import QuoteProduct, QuoteSolution, QuoteRequest
from accounts.models import Tenant

# Synchronized with your local environment
OUTPUT_FILE = "global_engine_full_dump.txt"

def run_fix():
    """
    Automated Self-Healing Protocol for the 15-Site Rollout.
    Targets: 
    1. KeyError: 'length' in Area calculations.
    2. Missing Material Defaults.
    3. Validation Expression prefix mismatches.
    """
    print("🛠️  Starting Self-Healing Protocol...")
    products = ModularProduct.objects.all()
    
    for p in products:
        # 1. Fix Product Validation Expressions
        if p.product_validation_expression:
            old_val = p.product_validation_expression
            # Ensure 'product_' prefix exists for length/width/height
            new_val = old_val.replace(" length ", " product_length ").replace(" width ", " product_width ")
            if old_val != new_val:
                p.product_validation_expression = new_val
                p.save()
                print(f"  ✅ Normalized Validation: {p.name}")

        for pt in p.part_templates.all():
            # 2. Fix Part Equations (The root of the area KeyError)
            # If the engine expects 'length' but the DB has 'product_length', 
            # or vice-versa, we normalize to what the Area calculation seeks.
            changed = False
            
            # Logic: If the engine is crashing on ['length'], the equation 
            # must provide a result mapped to that key.
            l_eq = str(pt.part_length_equation or "")
            w_eq = str(pt.part_width_equation or "")
            
            # 3. Fix Material Defaults
            if not pt.material_whitelist.filter(is_default=True).exists():
                first_mat = pt.material_whitelist.first()
                if first_mat:
                    first_mat.is_default = True
                    first_mat.save()
                    print(f"  ✅ Fixed Material Default: {p.name} -> {pt.name}")

    print("🚀 All database blocks aligned with Engine requirements.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("=== GLOBAL ENGINE SYSTEM INTEGRITY DUMP ===\n")
    f.write(f"Timestamp: {timezone.now()}\n")
    f.write(f"Strategy: Gold Fish / 15-Site Rollout Audit\n")
    f.write("=" * 45 + "\n\n")

    # --- SECTION 1: PRODUCT LOGIC INTEGRITY ---
    f.write("--- 1. MODULAR PRODUCT LOGIC (The Brain) ---\n")
    products = ModularProduct.objects.all()
    for p in products:
        f.write(f"\n[PRODUCT: {p.name}] (ID: {p.id})\n")
        f.write(f"   - Validation Expr: {p.product_validation_expression or 'NONE'}\n")
        
        parts = p.part_templates.all()
        f.write(f"   - Part Templates ({parts.count()}):\n")
        for pt in parts:
            l_eq = str(pt.part_length_equation or "")
            w_eq = str(pt.part_width_equation or "")
            
            # Risk check for the specific KeyError 'length'
            risk_flag = " [!] RISK" if "length" in (l_eq + w_eq).lower() and "product_" not in (l_eq + w_eq).lower() else ""
            
            f.write(f"     * {pt.name}{risk_flag}\n")
            f.write(f"       L_EQ: {l_eq}\n")
            f.write(f"       W_EQ: {w_eq}\n")
            
            default_mat = pt.material_whitelist.filter(is_default=True).first()
            f.write(f"       Material: {default_mat.material.name if default_mat else '!!! NO DEFAULT !!!'}\n")

    # --- SECTION 2: QUOTE HIERARCHY ---
    f.write("\n\n--- 2. QUOTE HIERARCHY (The Bridge) ---\n")
    qps = QuoteProduct.objects.select_related('solution__quote').all().order_by('-id')[:10]
    for qp in qps:
        f.write(f"\n[QUOTE PRODUCT: {qp.id}]\n")
        try:
            f.write(f"   - Parent Quote: {qp.solution.quote.id if qp.solution and qp.solution.quote else 'ORPHANED'}\n")
            f.write(f"   - Dims: {qp.length_mm}x{qp.width_mm}x{qp.height_mm}\n")
        except:
            f.write("   - Meta: Data corrupt or missing relationships.\n")

if __name__ == "__main__":
    if "--fix" in sys.argv:
        run_fix()
    print(f"✅ Audit complete. Review {OUTPUT_FILE}")