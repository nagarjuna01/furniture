


# class StockItem(models.Model):
#     #tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     material = GenericForeignKey()

#     base_billing_unit = models.ForeignKey(BillingUnit, on_delete=models.PROTECT)

# class MaterialRequirement(models.Model):
#     #tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

#     job = models.ForeignKey("Job", on_delete=models.CASCADE)

#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     material = GenericForeignKey()

#     required_qty = models.DecimalField(max_digits=10, decimal_places=3)
#     unit = models.ForeignKey(BillingUnit, on_delete=models.PROTECT)

#     wastage_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

#  

