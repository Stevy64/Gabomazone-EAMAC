from django.test import TestCase

# Create your tests here.
# if ProductImage.objects.all().filter(PRDIProduct=product_obj):
#     new_ProductImages_obj = ProductImage.objects.all().filter(PRDIProduct=product_obj)
#     print("new_ProductImages_obj:", new_ProductImages_obj.count())
#     counter = 0
#     for image in new_ProductImages_obj:
#         print(image.id)
#         new_ProductImages_obj = ProductImage.objects.get(
#             id=image.id)
#         print(new_ProductImages_obj.id)
#         if counter == 0:
#             if name_image_1:
#                 new_ProductImages_obj.PRDIImage = name_image_1
#                 new_ProductImages_obj.save()
#                 counter += 1
#                 continue
#         if counter == 1:
#             if name_image_2:
#                 new_ProductImages_obj.PRDIImage = name_image_2
#                 new_ProductImages_obj.save()
#                 counter += 1
#                 continue
#         if counter == 2:
#             if name_image_3:
#                 new_ProductImages_obj.PRDIImage = name_image_3
#                 new_ProductImages_obj.save()
#                 counter += 1
#                 continue
#         if counter == 3:
#             if name_image_4:
#                 new_ProductImages_obj.PRDIImage = name_image_4
#                 new_ProductImages_obj.save()
#                 counter += 1
#                 continue
# else:
#     print("llllol")
#     image_list = [name_image_1, name_image_2,
#                   name_image_3, name_image_4]
#     for image in image_list:
#         if image:
#             ProductImage.objects.create(
#                 PRDIProduct=new_product_obj,
#                 PRDIImage=image
#             )
