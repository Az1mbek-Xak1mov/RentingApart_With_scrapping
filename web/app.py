# from starlette.applications import Starlette
# from starlette_admin.contrib.sqla import Admin,ModelView
#
# from db.engine import engine
# from db.models import Owner, Renter, Apartment, LikedListing
#
# app=Starlette()
# admin=Admin(engine=engine,
#             title="Ijara",
#             base_url="/"
#             # auth_provider
# )
# admin.add_view(ModelView(Owner))
# admin.add_view(ModelView(Renter))
# admin.add_view(ModelView(Apartment))
# admin.add_view(ModelView(LikedListing))
#
# admin.mount_to(app)