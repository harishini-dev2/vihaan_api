from .views import * 

# Create your views here.

# -------------------------------------------------report-----------------------------------------------------------------------------------------

from django.db.models import Sum, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response

class PurchaseOrderReportAPI(APIView):
    def get(self, request):
        # Extract filter params
        po_id = request.query_params.get('po_id')
        category_id = request.query_params.get('category_id')
        style_id = request.query_params.get('style_id')
        school_id = request.query_params.get('school_id')  # NEW

        po_queryset = purchaseorder_table.objects.filter(is_active=1, status=1)

        if po_id:
            try:
                po_id = int(po_id)
                po_queryset = po_queryset.filter(id=po_id)
                if not po_queryset:
                    return response_switch(
                    "",
                    message="PO Not Exist",
                    data=[]
                    )
            except ValueError:
                return response_switch("bad_request", message="po_id must be an integer.", error=str(ValueError)) 

        if category_id:
            try:
                category_id = int(category_id)
                po_queryset = po_queryset.filter(category_id=category_id)
                if not po_queryset:
                    return response_switch(
                    "",
                    message="Category Not Exist",
                    data=[]
                    )
            except ValueError:
                return response_switch("bad_request", message="category_id must be an integer.", error=str(ValueError))

        if style_id:
            try:
                style_id = int(style_id)
                po_queryset = po_queryset.filter(style_id=style_id)
                if not po_queryset:
                    return response_switch(
                    "",
                    message="Style Not Exist",
                    data=[]
                    ) 
            except ValueError:
                return response_switch("bad_request", message="style_id must be an integer.", error=str(ValueError))

        if school_id:
            try:
                school_id = int(school_id)
                po_queryset = po_queryset.filter(school_id=school_id)
                if not po_queryset:
                    return response_switch(
                    "",
                    message="School Not Exist",
                    data=[]
                    )
            except ValueError:
                return response_switch("bad_request", message="school_id must be an integer.", error=str(ValueError))
                

        report_list = []

        for po in po_queryset:
            total_ordered_qty = po.total_quantity or 0

            deliveries = delivery_table.objects.filter(po_id=po.id, is_active=1, status=1)
            delivery_ids = deliveries.values_list('id', flat=True)

            total_delivered_qty = delivery_item_table.objects.filter(
                delivery_id__in=delivery_ids,
                is_active=1,
                status=1
            ).aggregate(total_delivered=Sum('quantity'))['total_delivered'] or 0

            balance_qty = total_ordered_qty - total_delivered_qty

            po_items = purchaseorder_item_table.objects.filter(po_id=po.id, is_active=1, status=1)
            delivered_per_item = delivery_item_table.objects.filter(
                delivery_id__in=delivery_ids,
                is_active=1,
                status=1
            ).values('box_packing_id').annotate(delivered_qty=Sum('quantity'))

            delivered_dict = {d['box_packing_id']: d['delivered_qty'] for d in delivered_per_item}

            # Fetch school short name
            school_obj = school_table.objects.filter(id=po.school_id).first()
            school_short_name = school_obj.short_name if school_obj else None

            # Fetch style code or short code
            style_obj = tm_style_table.objects.filter(id=po.style_id).first()
            style_code = getattr(style_obj, "code", None) or getattr(style_obj, "short_code", None) if style_obj else None

            items_status = []
            for item in po_items:
                delivered_qty = delivered_dict.get(item.id, 0)
                pending_qty = item.quantity - delivered_qty
                if pending_qty > 0:
                    size_obj = size_table.objects.filter(id=item.size_id).first()
                    color_obj = color_table.objects.filter(id=item.color_id).first()

                    size_name = size_obj.name if size_obj else None
                    color_name = color_obj.name if color_obj else None

                    items_status.append({
                        # "item_id": item.id,
                        # "description": item.description,
                        "size": size_name,
                        "color": color_name,
                        "ordered_quantity": item.quantity,
                        "delivered_quantity": delivered_qty,
                        "pending_quantity": pending_qty,
                    })

            report_list.append({
                "po_id": po.id,
                "po_number": po.po_number,
                "po_name": po.po_name,
                "school_short_name": school_short_name,  # NEW
                "style_code": style_code,                # NEW
                "total_ordered_quantity": total_ordered_qty,
                "total_delivered_quantity": total_delivered_qty,
                "balance_quantity": balance_qty,
                "pending_items": items_status,
            })
        
        return response_switch("success", message="Report listed successfully", data=report_list)


from collections import defaultdict

class DeliverySummaryAPI(APIView):
    def get(self, request):
        delivery_id = request.GET.get("delivery_id")
        if not delivery_id:
            return response_switch("bad_request", message="Missing delivery_id", data={"results": []})

        try:
            delivery_id = int(delivery_id)
        except ValueError:
            return response_switch("bad_request", message="Invalid delivery_id", data={"results": []})

        delivery = delivery_table.objects.filter(id=delivery_id, status=1).first()
        if not delivery:
            return response_switch("", message="Invalid delivery ID", data={"results": []})

        items = delivery_item_table.objects.filter(delivery_id=delivery_id, status=1)
        print("DEBUG: items count:", items.count())

        box_numbers = set()
        grouped_items = defaultdict(lambda: {"quantity": 0})

        po_item_ref = None
        po_ref = None

        for item in items:
            print("DEBUG: item:", item.id, "box_packing_id:", item.box_packing_id, "barcode:", item.barcode)

            box = boxpacking_table.objects.filter(id=item.box_packing_id, status=1).first()
            if not box:
                print("DEBUG: box not found or status !=1 for id", item.box_packing_id)
                continue
            box_numbers.add(box.box_number)

            box_item = boxpacking_item_table.objects.filter(box_packing_id=box.id, status=1).first()
            if not box_item:
                print("DEBUG: box_item not found or status !=1 for box_packing_id", box.id)
                continue

            po_item = None
            if box_item.barcode:
                barcode_trim = box_item.barcode.strip()
                po_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_trim).first()

            if not po_item and item.barcode:
                barcode_trim = item.barcode.strip()
                po_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_trim).first()

            if not po_item:
                print("DEBUG: skipping item because po_item not found")
                continue

            if po_item_ref is None:
                po_item_ref = po_item
                po_ref = purchaseorder_table.objects.filter(id=po_item.po_id).first()
                if not po_ref:
                    continue

            key = (po_item.size_id, po_item.color_id)
            try:
                grouped_items[key]["quantity"] += float(item.quantity or 0)
            except Exception as ex:
                print("DEBUG: error converting quantity:", item.quantity, ex)

        results = []
        for (size_id, color_id), info in grouped_items.items():
            size_name = get_fields_by_id(size_table, size_id, "name") or ""
            color_name = get_fields_by_id(color_table, color_id, "name") or ""
            results.append({
                "size": size_name,
                "color": color_name,
                "quantity": f"{info['quantity']:.2f}"
            })

        total_quantity = sum([float(r["quantity"]) for r in results]) if results else 0

        school_name = get_fields_by_id(school_table, po_ref.school_id, "name") if po_ref else ""
        style_name = get_fields_by_id(tm_style_table, po_ref.style_id, "name") if po_ref else ""

        data = {
            "count": len(results),
            "delivery_number": delivery.delivery_number,
            "box_number": list(box_numbers),
            "po_number": po_ref.po_number if po_ref else "",
            "school_name": school_name or "",
            "style_name": style_name or "",
            "total_quantity": total_quantity,
            "results": results
        }

        print(f"DEBUG: summary grouped result count: {len(results)}, total_quantity: {total_quantity}")
        print(f"DEBUG: boxes: {list(box_numbers)}")

        return response_switch(
            "success",
            message="Delivery summary fetched successfully",
            data=data
        )
