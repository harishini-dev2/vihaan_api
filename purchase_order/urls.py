from django.urls import path
from purchase_order.views import * 
from .packing import *  
from .box_packing import *  
from .delivery import *  
from .report import *  

urlpatterns=[
    
    # purchase_order
    path('school-style-list/', SchoolStyleList.as_view(), name='school-style-list'),
    path('style-details/', StyleDetails.as_view(), name='style-details'),
    path('purchaseorder-add/',PurchaseOrderAddAPIView.as_view(),name='purchaseorder-add'), 
    path('purchaseorder-list/',PurchaseOrderListAPIView.as_view(),name='purchaseorder-list'), 
    path('purchaseorder-details/',PurchaseOrderDetailAPIView.as_view(),name='purchaseorder-details'), 
    path('purchaseorder-update/',PurchaseOrderUpdate.as_view(),name='purchaseorder-update'),  
    path('purchaseorder-delete/',PurchaseOrderDeleteAPIView.as_view(),name='purchaseorder-delete'),
    path('purchaseorderitem-delete/',PurchaseOrderItemDeleteAPIView.as_view(),name='purchaseorderitem-delete'),
     
     
    # packing
    path('order-entry-add/', PackingAddAPIView.as_view(), name='order-entry-add'),
    path('order-entry-list/', PackingListAPIView.as_view(), name='order-entry-list'),
    path('order-entry-details/', PackingDetailAPIView.as_view(), name='order-entry-details'),
    path('order-entry-update/', PackingUpdateAPIView.as_view(), name='order-entry-update'), 
    path('order-entry-delete/', PackingDeleteAPIView.as_view(), name='order-entry-delete'), 
     
    # box_packing
    path('po-number/', PoNumberList.as_view(), name='po-number'),
    path('box-packing-add/', BoxPackingAddAPIView.as_view(), name='box-packing-add'),
    path('box-packing-list/', BoxPackingListAPIView.as_view() ,name='box-packing-list'),
    path('box-packing-details/', BoxPackingDetailAPIView.as_view(), name='box-packing-details'),
    path('box-packing-update/', BoxPackingUpdateAPIView.as_view(), name='box-packing-update'),
    path('tm-box-packing-delete/', BoxPackingTmDeleteAPIView.as_view() ,name='tm-box-packing-delete'),
    path('tx-box-packing-delete/', BoxPackingTxDeleteAPIView.as_view() ,name='tx-box-packing-delete'),

    # delivery
    path('delivery-add/', DeliveryAddAPIView.as_view(), name='delivery-add'),
    path('delivery-list/', DeliveryListAPIView.as_view(), name='delivery-list'),
    path('delivery-details/', DeliveryDetailAPIView.as_view(), name='delivery-details'),
    path('delivery-update/', DeliveryUpdateAPIView.as_view(), name='delivery-update'), 
    path('tm-delivery-delete/', DeliveryTmDeleteAPIView.as_view(), name='tm-delivery-delete'),
    path('tx-delivery-delete/', DeliveryTxDeleteAPIView.as_view(), name='tx-delivery-delete'),

    # report & summary
    path('report/', PurchaseOrderReportAPI.as_view(), name='report'),
    path('summary/', DeliverySummaryAPI.as_view(), name='summary'),
    


] 