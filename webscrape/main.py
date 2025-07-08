from webscrape.scrapping_urls_olx import get_all_urls_for_apart

def main():
    filter_url = "https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/?currency=UYE&search%5Bfilter_float_price:from%5D=600&search%5Bfilter_float_price:to%5D=900&search%5Bfilter_float_number_of_rooms:from%5D=2&search%5Bfilter_float_number_of_rooms:to%5D=3&search%5Bfilter_enum_furnished%5D%5B0%5D=yes&search%5Bfilter_enum_comission%5D%5B0%5D=no"

    count = get_all_urls_for_apart(filter_url)
    print(count)

if __name__ == "__main__":
    main()
