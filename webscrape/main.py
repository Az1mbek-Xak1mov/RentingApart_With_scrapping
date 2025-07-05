from webscrape.process_olx import process_olx_ad
from webscrape.scrapping_urls_olx import get_all_urls_for_apart

# Insert your OLX filter URL below:
filter_url = "https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/tashkent/?currency=UYE&search%5Bprivate_business%5D=private&search%5Bfilter_float_price:from%5D=300&search%5Bfilter_float_price:to%5D=600&search%5Bfilter_float_number_of_rooms:from%5D=1&search%5Bfilter_float_number_of_rooms:to%5D=3&search%5Bfilter_enum_comission%5D%5B0%5D=no"

result = get_all_urls_for_apart(filter_url)

if result:
    print(f"Processed")
else:
    print("No apartment processed.")
